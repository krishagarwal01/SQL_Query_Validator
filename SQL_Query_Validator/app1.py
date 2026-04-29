from collections import deque
from flask import Flask, render_template, request

from db_integration import database_file_path, execute_from_ast, get_connection
from injection import analyze_injection
from lexer import tokenize
from parser import Parser
from semantic import semantic_check
from parse_tree import parsed_to_tree, tree_to_text_lines
from sql_util import split_statements

app = Flask(__name__)
history = deque(maxlen=5)


# -------- Helper Functions -------- #

def suggest(query, err):
    q = query.upper()
    if "FROM" in err and q.startswith("SELECT"):
        return "Add FROM after columns."
    if "INTO" in err and q.startswith("INSERT"):
        return "INSERT must include INTO."
    if "does not exist" in err:
        return "Check table/column name."
    if "Unexpected" in err or "Expected" in err:
        return "Fix SQL syntax order."
    return "Check SQL syntax."


def highlight(query, err):
    if "Column '" in err or "Table '" in err:
        key = err.split("'")[1]
        pos = query.lower().find(key.lower())
        return query + "\n" + (" " * pos + "^") if pos != -1 else query
    return query


# -------- Core Processing -------- #

def process(query, run_db=True):
    get_connection()
    stmts = split_statements(query)

    results, valid, first_err = [], True, None

    for i, stmt in enumerate(stmts):
        stmt = stmt.strip()
        try:
            tokens = tokenize(stmt)
            ast = Parser(tokens).parse_statement()
            semantic_check(ast)

            tree = parsed_to_tree(ast)
            db_out = execute_from_ast(ast) if run_db else None

            results.append({
                "index": i + 1,
                "text": stmt,
                "valid": True,
                "parse": "\n".join(tree_to_text_lines(tree)),
                "db": db_out
            })

        except Exception as e:
            valid = False
            if not first_err:
                first_err = (stmt, str(e))

            results.append({
                "index": i + 1,
                "text": stmt,
                "valid": False,
                "error": str(e)
            })

    msg = "Valid Query" if valid else f"Error: {first_err[1]}"
    suggestion = suggest(*first_err) if first_err else ""
    highlight_q = highlight(*first_err) if first_err else ""

    return msg, results, suggestion, highlight_q, valid


# -------- Flask Route -------- #

@app.route("/", methods=["GET", "POST"])
def home():
    data = {
        "result": "", "suggestion": "", "highlight": "",
        "statements": [], "query": "", "valid": None
    }

    if request.method == "POST":
        q = request.form.get("query", "")
        run_db = request.form.get("run_db") == "1"

        res = process(q, run_db)

        data.update({
            "result": res[0],
            "statements": res[1],
            "suggestion": res[2],
            "highlight": res[3],
            "query": q,
            "valid": res[4]
        })

        history.appendleft({"query": q, "status": "Valid" if res[4] else "Error"})

    return render_template(
        "index.html",
        history=list(history),
        db_file=str(database_file_path()),
        **data
    )


if __name__ == "__main__":
    app.run(debug=True)
