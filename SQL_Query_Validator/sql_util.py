"""Split SQL text into individual statements (semicolons inside strings are ignored)."""

from typing import List


def split_statements(sql: str) -> List[str]:
    if not sql or not str(sql).strip():
        return []
    parts: List[str] = []
    current: List[str] = []
    in_single = False
    i = 0
    text = str(sql)
    n = len(text)
    while i < n:
        c = text[i]
        if c == "'":
            in_single = not in_single
            current.append(c)
        elif c == ";" and not in_single:
            stmt = "".join(current).strip()
            if stmt:
                parts.append(stmt)
            current = []
        else:
            current.append(c)
        i += 1
    stmt = "".join(current).strip()
    if stmt:
        parts.append(stmt)
    return parts
