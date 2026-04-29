# Sql-Validator-PBL 
# Mini SQL Query Validator

This project implements a basic SQL query validator using compiler design principles.

## Features
- Lexical Analysis using Flex
- Syntax Analysis using Bison
- Supports:
  - SELECT
  - INSERT
  - UPDATE
  - DELETE
- Error handling for invalid tokens and syntax errors

## How to Run

```bash
lex sql.l
yacc -d sql.y
gcc lex.yy.c y.tab.c -o sql_validator
./sql_validator

*/ PROJECT ARCHITECTURE OVERVIEW/*
The flow shows:

1. **Parser** (lexer.py + parser.py) → Breaks down the query into tokens and builds an AST (the structure)
2. **Semantic Check** (semantic.py) → Validates that `students` table exists, columns are valid, etc.
3. **Execution Engine** (db_integration.py) → Executes the validated query by:
   - Scanning the table
   - Filtering rows based on WHERE conditions
   - Projecting only requested columns
4. **Database** (SQLite) → Returns actual results

## Query Execution Flow

**SCAN students** → Reads the entire `students` table from the database into memory

**FILTER id = 1** → Applies the WHERE condition, keeping only rows matching `id = 1`

**PROJECT id, name** → Selects only the specific columns (`id, name`) instead of all columns

**RESULT** → Returns the final filtered and projected data to the user

## In Context of Your SQL Query Validator

This pipeline represents what happens when a query like this is executed:

```sql
SELECT id, name FROM students WHERE id = 1;
```
