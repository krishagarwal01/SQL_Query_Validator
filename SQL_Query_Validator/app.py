from collections import deque

from flask import Flask, render_template, request

from db_integration import database_file_path, execute_from_ast, get_connection
from injection import analyze_injection
from lexer import tokenize
from parse_tree import parsed_to_tree, tree_to_text_lines
from parser import Parser
from semantic import semantic_check
from sql_util import split_statements

app = Flask(__name__)
query_history = deque(maxlen=5)


def generate_suggestion(query, error_msg):
    query = query.strip()

    if "FROM" in error_msg and query.upper().startswith("SELECT"):
        return "Suggestion: Add the FROM keyword after the selected columns."

    if "INTO" in error_msg and query.upper().startswith("INSERT"):
        return "Suggestion: INSERT queries should include the INTO keyword."

    if "Table" in error_msg and "does not exist" in error_msg:
        return "Suggestion: Check whether the table name matches the predefined schema."

    if "Column" in error_msg and "does not exist" in error_msg:
        return "Suggestion: Verify the column name according to the table schema."

    if "Unexpected end of query" in error_msg:
        return "Suggestion: The query seems incomplete. Check for missing values, keywords, or conditions."

    if "Expected" in error_msg or "Unexpected token" in error_msg:
        return "Suggestion: Check the order of keywords and symbols in the query."

    return "Suggestion: Review the SQL syntax and schema details."


def highlight_error(query, error_msg):
    pointer_line = ""

    if "Column '" in error_msg:
        start = error_msg.find("Column '") + len("Column '")
        end = error_msg.find("'", start)
        wrong_col = error_msg[start:end]
        pos = query.lower().find(wrong_col.lower())
        if pos != -1:
            pointer_line = " " * pos + "^"

    elif "Table '" in error_msg:
        start = error_msg.find("Table '") + len("Table '")
        end = error_msg.find("'", start)
        wrong_table = error_msg[start:end]
        pos = query.lower().find(wrong_table.lower())
        if pos != -1:
            pointer_line = " " * pos + "^"

    elif "FROM" in error_msg:
        pos = len(query)
        pointer_line = " " * pos + "^"

    elif "INTO" in error_msg:
        pos = len("INSERT ")
        pointer_line = " " * pos + "^"

    if pointer_line:
        return query + "\n" + pointer_line

    return query


def _process_statements(current_query, run_db):
    """Returns dict with statements list, result summary, and error handling fields."""
    get_connection()
    parts = split_statements(current_query)
    global_injection = analyze_injection(current_query)

    if not parts:
        return {
            "result": "Enter at least one SQL statement.",
            "statements": [],
            "all_valid": False,
            "suggestion": "",
            "highlighted_query": "",
            "injection": global_injection,
            "run_db": run_db,
        }

    statement_rows = []
    all_valid = True
    first_error = None
    first_error_stmt = None

    for i, raw in enumerate(parts):
        raw_stripped = raw.strip()
        st_injection = analyze_injection(raw)
        tree_dict = None
        tree_text = ""
        err = None
        tokens = []
        db_out = None
        try:
            tokens = tokenize(raw_stripped)
            parser = Parser(tokens)
            ast = parser.parse_statement()
            if parser.current() is not None:
                raise Exception(f"Unexpected token after end of statement: {parser.current()!r}")
            semantic_check(ast)
            tree_dict = parsed_to_tree(ast)
            tree_text = "\n".join(tree_to_text_lines(tree_dict))
            if run_db:
                db_out = execute_from_ast(ast)
        except Exception as e:
            err = str(e)
            all_valid = False
            if first_error is None:
                first_error = err
                first_error_stmt = raw_stripped

        statement_rows.append(
            {
                "index": i + 1,
                "text": raw_stripped,
                "valid": err is None,
                "error": err,
                "tokens": tokens,
                "parse_tree": tree_dict,
                "parse_tree_text": tree_text,
                "injection": st_injection,
                "db": db_out,
            }
        )

    n = len(statement_rows)
    if all_valid:
        if n == 1:
            result = "Query is valid (syntax + schema)."
        else:
            result = f"All {n} statements are valid (syntax + schema)."
    else:
        result = f"Error: {first_error}" if first_error else "Error"

    suggestion = ""
    highlighted_query = ""
    if not all_valid and first_error_stmt is not None:
        suggestion = generate_suggestion(first_error_stmt, first_error)
        highlighted_query = highlight_error(first_error_stmt, first_error)

    return {
        "result": result,
        "statements": statement_rows,
        "all_valid": all_valid,
        "suggestion": suggestion,
        "highlighted_query": highlighted_query,
        "injection": global_injection,
        "run_db": run_db,
    }


@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    suggestion = ""
    highlighted_query = ""
    current_query = ""
    statements = []
    injection_report = None
    run_db = True
    all_valid = None

    if request.method == "POST":
        current_query = request.form.get("query", "")
        run_db = request.form.get("run_db") == "1"
        out = _process_statements(current_query, run_db)
        result = out["result"]
        statements = out["statements"]
        suggestion = out["suggestion"]
        highlighted_query = out["highlighted_query"]
        injection_report = out["injection"]
        all_valid = out["all_valid"]
        if out["statements"]:
            query_history.appendleft(
                {
                    "query": current_query,
                    "status": "Valid" if out["all_valid"] else "Error",
                }
            )

    return render_template(
        "index.html",
        result=result,
        suggestion=suggestion,
        highlighted_query=highlighted_query,
        history=list(query_history),
        current_query=current_query,
        statements=statements,
        injection_report=injection_report,
        run_db=run_db,
        all_valid=all_valid,
        db_file_path=str(database_file_path()),
    )


if __name__ == "__main__":
    app.run(debug=True)
