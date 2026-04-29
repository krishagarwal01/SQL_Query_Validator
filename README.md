# SQL Query Validator

A SQL query validator and parser built with **Flex + Bison + C**.  
It validates SQL syntax, performs semantic checks, detects basic injection patterns, and returns JSON output.

## Features

- Parses a SQL subset: `SELECT`, `INSERT`, `UPDATE`, `DELETE`
- Generates token stream and AST-like JSON response
- Performs semantic checks for table/column validity
- Includes basic SQL injection risk analysis
- Supports command-line usage and a simple browser UI

## Project Structure

- `sql.l` - Flex lexer rules
- `sql.y` - Bison grammar and parser actions
- `main_json.c` - Main entrypoint (JSON output)
- `semantic.c` - Semantic validation logic
- `injection.c` - Injection detection logic
- `build.ps1` - Build script
- `run.ps1` - Run parser script
- `start.ps1` - Build + run helper
- `start-ui.ps1` - Build + start UI server
- `ui/server.js` - Node server for web UI

## Complete File-by-File Reference

### Folders

`ui/`  
Contains the browser UI files and Node HTTP server used for interactive validation.  
Performs frontend rendering and API handling for `/api/validate`.

`__pycache__/`  
Stores Python bytecode cache files created by Python runtime, if any Python scripts are used.  
Performs no runtime project logic and can be safely ignored for normal usage.

### Root files

`README.md`  
Contains setup, build, run, UI, and troubleshooting instructions for this project.  
Performs documentation function only; no runtime logic.

`Makefile`  
Defines build rules for generating parser sources and compiling executable binaries.  
Performs orchestration of `bison`, `flex`, `gcc`, and clean targets.

`build.ps1`  
PowerShell helper that calls MSYS2 bash and runs `make CC=gcc`.  
Performs one-command project build from Windows PowerShell.

`run.ps1`  
PowerShell helper that runs `sqlparse_json.exe` using `input.sql` or `-Query`.  
Performs command-line parsing execution and output forwarding.

`start.ps1`  
PowerShell helper that first builds the project and then runs parser execution.  
Performs build-and-run workflow in a single command.

`clean.ps1`  
PowerShell helper that calls `make clean` via MSYS2 bash path.  
Performs cleanup of generated parser and binary artifacts.

`start-ui.ps1`  
PowerShell helper that checks Node.js, builds parser, then starts UI server.  
Performs complete UI startup pipeline for local browser testing.

`input.sql`  
Sample SQL script with valid queries for parser and semantic checks.  
Performs test input role for quick verification of parser behavior.

`driver.h`  
Declares parser-driver APIs for token capture, JSON helpers, and parse entrypoint.  
Performs interface contract between lexer, parser, and main program.

`driver.c`  
Implements parse orchestration, token JSON collection, and output composition.  
Performs conversion of parser results into final JSON response payload.

`semantic.h`  
Declares schema validation functions for table and column existence checks.  
Performs semantic-check interface for grammar actions in parser.

`semantic.c`  
Implements an in-memory schema (`students`, `courses`, `teachers`) and validators.  
Performs semantic enforcement like valid table, valid column, and column counts.

`injection.h`  
Declares SQL injection analysis function returning JSON risk report.  
Performs interface exposure for injection scanning module.

`injection.c`  
Implements pattern-based SQL injection detection with risk levels and findings.  
Performs static payload scanning and generates JSON findings/snippet output.

`main_json.c`  
Reads SQL text from stdin, invokes parser, and prints JSON to stdout.  
Performs CLI executable entrypoint for both scripts and UI subprocess calls.

`sql.l`  
Defines lexer/tokenizer rules for keywords, identifiers, literals, and operators.  
Performs lexical analysis and sends tokens to Bison parser.

`sql.y`  
Defines grammar for `SELECT`, `INSERT`, `UPDATE`, and `DELETE` SQL subset.  
Performs syntax parsing, semantic checks, and AST JSON object construction.

`student.css`  
Currently an empty placeholder stylesheet file in project root.  
Performs no active function unless future UI styling is moved here.

`student.xls`  
Currently an empty placeholder spreadsheet file in project root.  
Performs no active function in parser or UI runtime.

### Generated build artifacts

`lex.yy.c`  
Auto-generated C lexer source produced from `sql.l` by Flex.  
Performs scanner implementation at compile/runtime and should not be hand-edited.

`sql.tab.c`  
Auto-generated C parser source produced from `sql.y` by Bison.  
Performs parser state machine implementation and should not be hand-edited.

`sql.tab.h`  
Auto-generated parser header containing token definitions and parser types.  
Performs shared token/type declarations used by lexer and driver.

`sqlparse_json.exe`  
Compiled Windows executable generated from parser, lexer, and helper C files.  
Performs actual SQL validation process when called by scripts or UI server.

### UI files

`ui/server.js`  
Node.js HTTP server that serves HTML and calls `sqlparse_json.exe` as subprocess.  
Performs validation API, demo in-memory query execution, and response shaping.

`ui/index.html`  
Single-page frontend that submits SQL and renders status/tokens/AST/results.  
Performs user interaction, fetch calls, and rich result visualization.

## Requirements

### 1) Windows tools

- [MSYS2](https://www.msys2.org/) (for `gcc`, `bison`, `flex`, `make`)
- [Node.js LTS](https://nodejs.org/) (for UI only)
- PowerShell

### 2) Install compiler/parser tools in MSYS2

Open **MSYS2 MinGW UCRT64** terminal and run:

```bash
pacman -Syu
```

If prompted to restart MSYS2, close and reopen **MSYS2 UCRT64**, then run:

```bash
pacman -Syu
```

Install required packages:

```bash
pacman -S --needed mingw-w64-ucrt-x86_64-toolchain flex bison make
```

When it asks for toolchain package selection, press **Enter** (default: all).

## Build and Run (PowerShell)

Open PowerShell in this project folder.

If script execution is blocked, enable it for the current shell only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Build

```powershell
.\build.ps1 -MsysShell "C:\msys64\usr\bin\bash.exe"
```

### Run using default SQL file (`input.sql`)

```powershell
.\run.ps1
```

### Run with a single query

```powershell
.\run.ps1 -Query "SELECT id, name FROM students WHERE age >= 18;"
```

### Build + run in one command

```powershell
.\start.ps1
.\start.ps1 -Query "SELECT id, name FROM students WHERE age >= 18;"
```

### Clean generated/build files

```powershell
.\clean.ps1 -MsysShell "C:\msys64\usr\bin\bash.exe"
```

## Run the Web UI

Quick command to run the UI:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-ui.ps1 -MsysShell "C:\msys64\usr\bin\bash.exe"
```

Make sure Node.js is installed and available:

```powershell
node -v
npm -v
```

Start the UI server (run both commands):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-ui.ps1 -MsysShell "C:\msys64\usr\bin\bash.exe"
```

Open:

- [http://localhost:3000](http://localhost:3000)

## If MSYS2 is installed in a custom location

Pass your actual bash path:

```powershell
.\build.ps1 -MsysShell "D:\tools\msys64\usr\bin\bash.exe"
.\start.ps1 -MsysShell "D:\tools\msys64\usr\bin\bash.exe"
.\clean.ps1 -MsysShell "D:\tools\msys64\usr\bin\bash.exe"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-ui.ps1 -MsysShell "D:\tools\msys64\usr\bin\bash.exe"
```

## Expected Output Format

The parser prints JSON like:

- `ok` - parse success/failure
- `tokens` - lexical tokens
- `semantic` - semantic validation result
- `injection` - injection risk summary
- `ast` - parsed statements

## Troubleshooting

### PowerShell says scripts are disabled

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### `Node.js is not installed or not in PATH`

- Reopen terminal/Cursor after Node install
- Verify with:

```powershell
node -v
npm -v
```

### MSYS2 package install fails with `not enough free disk space`

- Free disk space on the MSYS2 install drive (usually `C:`)
- Retry package installation in MSYS2 UCRT64 terminal

### Build fails because MSYS bash path is wrong

- Verify `bash.exe` path exists
- Pass correct path using `-MsysShell`
