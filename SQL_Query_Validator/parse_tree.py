"""
Build a display tree from the parser's AST (nested dict/list structure).
Suitable for rendering as a nested list / text parse tree in the UI.
"""


def _leaf(label: str) -> dict:
    return {"label": label, "children": []}


def _node(label: str, children: list) -> dict:
    return {"label": label, "children": children}


def _format_condition(cond: dict) -> list[dict]:
    if not cond:
        return [_leaf("condition: (none)")]
    return [
        _node(
            "condition",
            [
                _leaf(f"column: {cond['column']}"),
                _leaf(f"operator: {cond['operator']}"),
                _leaf(f"value: {cond['value']!r}"),
            ],
        )
    ]


def parsed_to_tree(parsed: dict) -> dict:
    """Root node wraps the statement kind and structured children."""
    qtype = parsed.get("type", "?")
    if qtype == "SELECT":
        col_nodes = [
            _leaf("columns: *")
            if parsed["columns"] == ["*"]
            else _node("columns", [_leaf(f"{c}") for c in parsed["columns"]])
        ]
        body: list[dict] = [
            _leaf("type: SELECT"),
            *col_nodes,
            _leaf(f"table: {parsed['table']}"),
            *_format_condition(parsed.get("condition")),
        ]
        return _node("Query", [_node("SELECT", body)])

    if qtype == "INSERT":
        vals = [ _leaf(f"{v!r}") for v in parsed["values"]]
        body = [
            _leaf("type: INSERT"),
            _leaf(f"table: {parsed['table']}"),
            _node("VALUES", vals),
        ]
        return _node("Query", [_node("INSERT", body)])

    if qtype == "UPDATE":
        set_nodes = [
            _leaf(f"column: {parsed['set_column']}"),
            _leaf(f"value: {parsed['set_value']!r}"),
        ]
        body = [
            _leaf("type: UPDATE"),
            _leaf(f"table: {parsed['table']}"),
            _node("SET", set_nodes),
            *_format_condition(parsed.get("condition")),
        ]
        return _node("Query", [_node("UPDATE", body)])

    if qtype == "DELETE":
        body = [
            _leaf("type: DELETE"),
            _leaf(f"table: {parsed['table']}"),
            *_format_condition(parsed.get("condition")),
        ]
        return _node("Query", [_node("DELETE", body)])

    return _node("Query", [_leaf(f"Unknown: {parsed!r}")])


def tree_to_text_lines(node: dict, prefix: str = "", is_last: bool = True, is_root: bool = True) -> list[str]:
    """ASCII tree text (for <pre> fallback and accessibility)."""
    lines: list[str] = []
    connector = "" if is_root else ("└── " if is_last else "├── ")
    label = node.get("label", "")
    lines.append(prefix + connector + label)
    if not is_root:
        extension = "    " if is_last else "│   "
        next_prefix = prefix + extension
    else:
        next_prefix = prefix
    ch = node.get("children") or []
    for i, c in enumerate(ch):
        last = i == len(ch) - 1
        lines.extend(tree_to_text_lines(c, next_prefix, last, is_root=False))
    return lines
