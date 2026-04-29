"""
SQLite integration: file-based database under `data/demo.db` (aligned with `schema.SCHEMA`).
SELECT / INSERT / UPDATE / DELETE are executed only from a validated AST (identifiers whitelisted).

Delete `data/demo.db` to reset tables and seed data.
"""

import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

from schema import SCHEMA

_conn: Optional[sqlite3.Connection] = None

# Project folder / data/demo.db — open this file in DB Browser for SQLite or VS Code SQLite viewers.
DB_PATH = Path(__file__).resolve().parent / "data" / "demo.db"


def _ensure_schema_and_seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        ("students",),
    )
    if cur.fetchone() is not None:
        return
    for table, cols in SCHEMA.items():
        col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
        cur.execute(f'CREATE TABLE "{table}" ({col_defs})')
    conn.commit()
    cur.executemany(
        'INSERT INTO "students" VALUES (?,?,?,?)',
        [
            ("1", "Alice", "20", "1"),
            ("2", "Bob", "22", "2"),
        ],
    )
    cur.executemany(
        'INSERT INTO "courses" VALUES (?,?)',
        [("1", "Database Systems"), ("2", "Algorithms")],
    )
    cur.executemany(
        'INSERT INTO "teachers" VALUES (?,?,?)',
        [("1", "Dr. Smith", "Databases")],
    )
    conn.commit()


def get_connection() -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        return _conn
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _ensure_schema_and_seed(_conn)
    return _conn


def database_file_path() -> Path:
    """Absolute path to the SQLite file (for UI / docs)."""
    return DB_PATH.resolve()


def _quote_ident(name: str) -> str:
    if not name or not isinstance(name, str):
        raise ValueError("Invalid identifier")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError("Invalid identifier")
    return '"' + name.replace('"', '""') + '"'


def _ensure_table_col(table: str, col: str) -> None:
    if table not in SCHEMA:
        raise ValueError("Invalid table for execution")
    if col not in SCHEMA[table]:
        raise ValueError("Invalid column for execution")


def _cast_value(s: str) -> Any:
    t = s.strip()
    if t.isdigit() or (t.startswith("-") and t[1:].isdigit()):
        return int(t)
    return t


def _format_executed(q: str, params: list[Any]) -> str:
    """Readable SQL for UI (values substituted; safe here because AST is whitelisted)."""
    if not params:
        return q
    parts: list[str] = []
    for p in params:
        if isinstance(p, str):
            parts.append("'" + p.replace("'", "''") + "'")
        else:
            parts.append(str(p))
    if q.count("?") == len(parts):
        out = q
        for s in parts:
            out = out.replace("?", s, 1)
        return out
    return q + "\n-- parameters: " + ", ".join(parts)


def execute_from_ast(ast: dict) -> dict:
    """
    Run a whitelisted command from a parsed+semantically valid AST.
    Returns { ok, type, error?, columns?, rows?, rowcount? }.
    """
    conn = get_connection()
    cur = conn.cursor()
    t = ast["type"]
    try:
        if t == "SELECT":
            table = ast["table"]
            if table not in SCHEMA:
                return {"ok": False, "type": t, "error": "Invalid table"}
            cols = ast["columns"]
            if cols == ["*"]:
                col_sql = "*"
            else:
                for c in cols:
                    _ensure_table_col(table, c)
                col_sql = ", ".join(_quote_ident(c) for c in cols)
            q = f'SELECT {col_sql} FROM {_quote_ident(table)}'
            params: list[Any] = []
            cond = ast.get("condition")
            if cond:
                ccol = cond["column"]
                _ensure_table_col(table, ccol)
                op = cond["operator"]
                if op not in ("=", ">", "<", ">=", "<=", "!="):
                    return {"ok": False, "type": t, "error": "Unsupported operator for DB run"}
                val = cond["value"]
                if isinstance(val, str) and (val.isdigit() or (val.startswith("-") and val[1:].isdigit())):
                    use = int(val)
                else:
                    use = _cast_value(str(val)) if not isinstance(val, (int, float)) else val
                q += f" WHERE {_quote_ident(ccol)} {op} ?"
                params.append(use)
            cur.execute(q, params)
            rows = cur.fetchall()
            col_names = [d[0] for d in cur.description] if cur.description else []
            return {
                "ok": True,
                "type": t,
                "columns": col_names,
                "rows": [list(r) for r in rows],
                "executed_display": _format_executed(q, params),
            }

        if t == "INSERT":
            table = ast["table"]
            if table not in SCHEMA:
                return {"ok": False, "type": t, "error": "Invalid table"}
            if len(ast["values"]) != len(SCHEMA[table]):
                return {"ok": False, "type": t, "error": "Value count mismatch"}
            placeholders = ", ".join(["?"] * len(ast["values"]))
            cols = ", ".join(_quote_ident(c) for c in SCHEMA[table])
            vals: list[Any] = []
            for v, cname in zip(ast["values"], SCHEMA[table]):
                vals.append(_cast_value(str(v)) if not isinstance(v, (int, float)) else v)
            q = f'INSERT INTO {_quote_ident(table)} ({cols}) VALUES ({placeholders})'
            cur.execute(q, vals)
            conn.commit()
            return {
                "ok": True,
                "type": t,
                "rowcount": cur.rowcount,
                "message": f"Inserted {cur.rowcount} row(s)" if cur.rowcount else "No row inserted",
                "executed_display": _format_executed(q, vals),
            }

        if t == "UPDATE":
            table = ast["table"]
            if table not in SCHEMA:
                return {"ok": False, "type": t, "error": "Invalid table"}
            s_col = ast["set_column"]
            _ensure_table_col(table, s_col)
            set_val = ast["set_value"]
            s_use = _cast_value(str(set_val)) if not isinstance(set_val, (int, float)) else set_val
            cond = ast.get("condition")
            if not cond:
                return {"ok": False, "type": t, "error": "Refusing unbounded UPDATE (no WHERE)"}
            ccol = cond["column"]
            _ensure_table_col(table, ccol)
            op = cond["operator"]
            if op != "=":
                return {"ok": False, "type": t, "error": "UPDATE execution supports WHERE = only in demo"}
            wval = cond["value"]
            w_use = _cast_value(str(wval)) if not isinstance(wval, (int, float)) else wval
            q = f'UPDATE {_quote_ident(table)} SET {_quote_ident(s_col)} = ? WHERE {_quote_ident(ccol)} = ?'
            cur.execute(q, [s_use, w_use])
            conn.commit()
            return {
                "ok": True,
                "type": t,
                "rowcount": cur.rowcount,
                "message": f"Updated {cur.rowcount} row(s)",
                "executed_display": _format_executed(q, [s_use, w_use]),
            }

        if t == "DELETE":
            table = ast["table"]
            if table not in SCHEMA:
                return {"ok": False, "type": t, "error": "Invalid table"}
            cond = ast.get("condition")
            if not cond:
                return {"ok": False, "type": t, "error": "Refusing unbounded DELETE (no WHERE)"}
            ccol = cond["column"]
            _ensure_table_col(table, ccol)
            op = cond["operator"]
            if op != "=":
                return {"ok": False, "type": t, "error": "DELETE execution supports WHERE = only in demo"}
            wval = cond["value"]
            w_use = _cast_value(str(wval)) if not isinstance(wval, (int, float)) else wval
            q = f'DELETE FROM {_quote_ident(table)} WHERE {_quote_ident(ccol)} = ?'
            cur.execute(q, [w_use])
            conn.commit()
            return {
                "ok": True,
                "type": t,
                "rowcount": cur.rowcount,
                "message": f"Deleted {cur.rowcount} row(s)",
                "executed_display": _format_executed(q, [w_use]),
            }

        return {"ok": False, "type": t, "error": "Unsupported statement for execution"}
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return {"ok": False, "type": t, "error": str(e)}
