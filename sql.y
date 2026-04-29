/* Bison: SQL subset + JSON AST for Python UI.
 * Build: bison -d sql.y && flex sql.l && cc -o sqlparse_json sql.tab.c lex.yy.c driver.c
 */
%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "driver.h"
#include "semantic.h"

extern char *g_program_stmts_json;
int yylex(void);
void yyerror(const char *s);
static int g_value_list_count = 0;
static char *g_where_column = NULL;
static char **g_select_columns = NULL;
static int g_select_column_count = 0;
static int g_select_star = 0;

static void reset_select_columns(void)
{
    int i;
    for (i = 0; i < g_select_column_count; i++) {
        free(g_select_columns[i]);
    }
    free(g_select_columns);
    g_select_columns = NULL;
    g_select_column_count = 0;
    g_select_star = 0;
}

static int add_select_column(const char *name)
{
    char **next = (char **)realloc(g_select_columns, sizeof(char *) * (g_select_column_count + 1));
    if (!next) {
        return 0;
    }
    g_select_columns = next;
    g_select_columns[g_select_column_count] = strdup(name ? name : "");
    if (!g_select_columns[g_select_column_count]) {
        return 0;
    }
    g_select_column_count++;
    return 1;
}
%}

%error-verbose

%union {
    char *str;
    int num;
}

%token <str> IDENTIFIER NUMBER STRING
%token SELECT FROM WHERE INSERT INTO VALUES UPDATE SET DELETE
%token EQ NE LE GE LT GT
%token COMMA SEMICOLON LPAREN RPAREN STAR

%type <str> program stmt_list_opt stmt_list stmt select_stmt select_list column_list
%type <str> opt_where relop literal value_list insert_stmt update_stmt delete_stmt

%start program

%%

program
    : stmt_list_opt { g_program_stmts_json = $1; }
    ;

stmt_list_opt
    : /* empty */ { $$ = strdup(""); }
    | stmt_list   { $$ = $1; }
    ;

stmt_list
    : stmt { $$ = $1; }
    | stmt_list SEMICOLON stmt {
        $$ = dj_aprintf("%s,%s", $1, $3);
        free($1);
        free($3);
      }
    | stmt_list SEMICOLON { $$ = $1; }
    ;

stmt
    : select_stmt { $$ = $1; }
    | insert_stmt { $$ = $1; }
    | update_stmt { $$ = $1; }
    | delete_stmt { $$ = $1; }
    ;

select_stmt
    : SELECT select_list FROM IDENTIFIER opt_where {
        int i;
        if (!schema_table_exists($4)) {
            yyerror(dj_aprintf("Table '%s' does not exist", $4));
            free($2);
            free($4);
            free($5);
            reset_select_columns();
            YYERROR;
        }
        if (!g_select_star) {
            for (i = 0; i < g_select_column_count; i++) {
                if (!schema_column_exists($4, g_select_columns[i])) {
                    yyerror(dj_aprintf("Column '%s' does not exist in table '%s'", g_select_columns[i], $4));
                    free($2);
                    free($4);
                    free($5);
                    reset_select_columns();
                    YYERROR;
                }
            }
        }
        if (g_where_column && !schema_column_exists($4, g_where_column)) {
            yyerror(dj_aprintf("Column '%s' does not exist in table '%s'", g_where_column, $4));
            free($2);
            free($4);
            free($5);
            free(g_where_column);
            g_where_column = NULL;
            reset_select_columns();
            YYERROR;
        }
        char *tj = dj_json_string($4);
        $$ = dj_aprintf("{\"type\":\"SELECT\",\"columns\":%s,\"table\":%s,\"condition\":%s}", $2, tj, $5);
        free($2);
        free($4);
        free($5);
        free(tj);
        free(g_where_column);
        g_where_column = NULL;
        reset_select_columns();
      }
    ;

select_list
    : STAR {
        reset_select_columns();
        g_select_star = 1;
        $$ = strdup("[\"*\"]");
      }
    | column_list { $$ = $1; }
    ;

column_list
    : IDENTIFIER {
        char *jq = dj_json_string($1);
        if (g_select_column_count == 0) {
            reset_select_columns();
        }
        if (!add_select_column($1)) {
            yyerror("out of memory");
            free($1);
            free(jq);
            YYERROR;
        }
        $$ = dj_aprintf("[%s]", jq);
        free($1);
        free(jq);
      }
    | column_list COMMA IDENTIFIER {
        char *jq = dj_json_string($3);
        if (!add_select_column($3)) {
            yyerror("out of memory");
            free($1);
            free($3);
            free(jq);
            YYERROR;
        }
        $$ = dj_aprintf("%.*s,%s]", (int)(strlen($1) - 1), $1, jq);
        free($1);
        free($3);
        free(jq);
      }
    ;

opt_where
    : /* empty */ {
        free(g_where_column);
        g_where_column = NULL;
        $$ = strdup("null");
      }
    | WHERE IDENTIFIER relop literal {
        free(g_where_column);
        g_where_column = strdup($2);
        char *jc = dj_json_string($2);
        $$ = dj_aprintf("{\"column\":%s,\"operator\":\"%s\",\"value\":%s}", jc, $3, $4);
        free($2);
        free($3);
        free($4);
        free(jc);
      }
    ;

relop
    : EQ { $$ = strdup("="); }
    | GT { $$ = strdup(">"); }
    | LT { $$ = strdup("<"); }
    | GE { $$ = strdup(">="); }
    | LE { $$ = strdup("<="); }
    | NE { $$ = strdup("!="); }
    ;

literal
    : IDENTIFIER { $$ = dj_json_string($1); free($1); }
    | NUMBER     { $$ = dj_json_string($1); free($1); }
    | STRING     { $$ = dj_json_string($1); free($1); }
    ;

insert_stmt
    : INSERT INTO IDENTIFIER VALUES LPAREN value_list RPAREN {
        if (!schema_table_exists($3)) {
            yyerror(dj_aprintf("Table '%s' does not exist", $3));
            free($3);
            free($6);
            YYERROR;
        }
        if (g_value_list_count != schema_column_count($3)) {
            yyerror("Number of values does not match table columns");
            free($3);
            free($6);
            YYERROR;
        }
        char *tj = dj_json_string($3);
        $$ = dj_aprintf("{\"type\":\"INSERT\",\"table\":%s,\"values\":%s}", tj, $6);
        free($3);
        free($6);
        free(tj);
      }
    ;

value_list
    : literal {
        g_value_list_count = 1;
        $$ = dj_aprintf("[%s]", $1);
        free($1);
      }
    | value_list COMMA literal {
        g_value_list_count++;
        $$ = dj_aprintf("%.*s,%s]", (int)(strlen($1) - 1), $1, $3);
        free($1);
        free($3);
      }
    ;

update_stmt
    : UPDATE IDENTIFIER SET IDENTIFIER EQ literal opt_where {
        if (!schema_table_exists($2)) {
            yyerror(dj_aprintf("Table '%s' does not exist", $2));
            free($2);
            free($4);
            free($6);
            free($7);
            YYERROR;
        }
        if (!schema_column_exists($2, $4)) {
            yyerror(dj_aprintf("Column '%s' does not exist in table '%s'", $4, $2));
            free($2);
            free($4);
            free($6);
            free($7);
            YYERROR;
        }
        if (g_where_column && !schema_column_exists($2, g_where_column)) {
            yyerror(dj_aprintf("Column '%s' does not exist in table '%s'", g_where_column, $2));
            free($2);
            free($4);
            free($6);
            free($7);
            free(g_where_column);
            g_where_column = NULL;
            YYERROR;
        }
        char *t1 = dj_json_string($2);
        char *sc = dj_json_string($4);
        $$ = dj_aprintf(
            "{\"type\":\"UPDATE\",\"table\":%s,\"set_column\":%s,\"set_value\":%s,\"condition\":%s}",
            t1, sc, $6, $7);
        free($2);
        free($4);
        free($6);
        free($7);
        free(t1);
        free(sc);
        free(g_where_column);
        g_where_column = NULL;
      }
    ;

delete_stmt
    : DELETE FROM IDENTIFIER opt_where {
        if (!schema_table_exists($3)) {
            yyerror(dj_aprintf("Table '%s' does not exist", $3));
            free($3);
            free($4);
            YYERROR;
        }
        if (g_where_column && !schema_column_exists($3, g_where_column)) {
            yyerror(dj_aprintf("Column '%s' does not exist in table '%s'", g_where_column, $3));
            free($3);
            free($4);
            free(g_where_column);
            g_where_column = NULL;
            YYERROR;
        }
        char *tj = dj_json_string($3);
        $$ = dj_aprintf("{\"type\":\"DELETE\",\"table\":%s,\"condition\":%s}", tj, $4);
        free($3);
        free($4);
        free(tj);
        free(g_where_column);
        g_where_column = NULL;
      }
    ;

%%
