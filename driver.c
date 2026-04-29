#include "driver.h"
#include "sql.tab.h"
#include "injection.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int yylex(void);
extern int yyparse(void);

typedef struct yy_buffer_state *YY_BUFFER_STATE;
extern YY_BUFFER_STATE yy_scan_string(const char *str);
extern void yy_delete_buffer(YY_BUFFER_STATE buffer);

char *g_parse_err = NULL;
char *g_program_stmts_json = NULL;

void yyerror(const char *s)
{
    free(g_parse_err);
    g_parse_err = s ? strdup(s) : strdup("parse error");
}

static char *tok_json = NULL;
static int tok_first = 1;

void yacc_reset_tokens(void)
{
    free(tok_json);
    tok_json = malloc(2);
    if (tok_json)
        strcpy(tok_json, "[");
    tok_first = 1;
}

static void tok_cat(const char *s)
{
    size_t L = strlen(tok_json);
    size_t n = strlen(s);
    tok_json = (char *)realloc(tok_json, L + n + 1);
    memcpy(tok_json + L, s, n + 1);
}

void yacc_record_token(int token, const char *yytext)
{
    const char *t = yytext ? yytext : "";
    const char *kind = "INVALID";
    switch (token) {
    case SELECT:
    case FROM:
    case WHERE:
    case INSERT:
    case INTO:
    case VALUES:
    case UPDATE:
    case SET:
    case DELETE:
        kind = "KEYWORD";
        break;
    case EQ:
    case NE:
    case LE:
    case GE:
    case LT:
    case GT:
        kind = "OPERATOR";
        break;
    case COMMA:
    case SEMICOLON:
    case LPAREN:
    case RPAREN:
    case STAR:
        kind = "SYMBOL";
        break;
    case NUMBER:
        kind = "NUMBER";
        break;
    case STRING:
        kind = "STRING";
        break;
    case IDENTIFIER:
        kind = "IDENTIFIER";
        break;
    default:
        break;
    }
    if (!tok_json)
        yacc_reset_tokens();
    if (!tok_first)
        tok_cat(",");
    tok_first = 0;
    tok_cat("[\"");
    tok_cat(kind);
    tok_cat("\",\"");
    /* escape minimal for second field */
    for (const unsigned char *p = (const unsigned char *)t; *p; p++) {
        if (*p == '"' || *p == '\\') {
            tok_cat("\\");
            char b[2] = {(char)*p, 0};
            tok_cat(b);
        } else if (*p == '\n') {
            tok_cat("\\n");
        } else {
            char b[2] = {(char)*p, 0};
            tok_cat(b);
        }
    }
    tok_cat("\"]");
}

const char *yacc_tokens_json_finish(void)
{
    if (!tok_json) {
        static char e[] = "[]";
        return e;
    }
    tok_cat("]");
    return tok_json;
}

char *dj_aprintf(const char *fmt, ...)
{
    char tmp[16384];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(tmp, sizeof tmp, fmt, ap);
    va_end(ap);
    return strdup(tmp);
}

char *dj_json_string(const char *raw)
{
    if (!raw)
        raw = "";
    size_t cap = strlen(raw) * 2 + 3;
    char *o = (char *)malloc(cap);
    if (!o)
        return strdup("\"\"");
    size_t j = 0;
    o[j++] = '"';
    for (const unsigned char *p = (const unsigned char *)raw; *p; p++) {
        if (j + 4 >= cap) {
            cap *= 2;
            o = (char *)realloc(o, cap);
        }
        if (*p == '"' || *p == '\\') {
            o[j++] = '\\';
            o[j++] = (char)*p;
        } else if (*p == '\n') {
            o[j++] = '\\';
            o[j++] = 'n';
        } else if (*p == '\r') {
            o[j++] = '\\';
            o[j++] = 'r';
        } else {
            o[j++] = (char)*p;
        }
    }
    o[j++] = '"';
    o[j] = '\0';
    return o;
}

char *parse_sql_to_json(const char *input, char **err_out)
{
    free(g_parse_err);
    g_parse_err = NULL;
    free(g_program_stmts_json);
    g_program_stmts_json = NULL;
    yacc_reset_tokens();

    if (!input)
        input = "";

    YY_BUFFER_STATE buf = yy_scan_string(input);
    int r = yyparse();
    yy_delete_buffer(buf);

    if (r != 0) {
        if (err_out)
            *err_out = g_parse_err ? strdup(g_parse_err) : strdup("parse error");
        free(tok_json);
        tok_json = NULL;
        free(g_program_stmts_json);
        g_program_stmts_json = NULL;
        return NULL;
    }

    const char *toks = yacc_tokens_json_finish();
    const char *stmts = g_program_stmts_json ? g_program_stmts_json : "";
    char *inj = analyze_injection_json(input);
    size_t n = strlen(toks) + strlen(stmts) + strlen(inj) + 256;
    char *out = (char *)malloc(n);
    if (!out) {
        if (err_out)
            *err_out = strdup("out of memory");
        free(tok_json);
        tok_json = NULL;
        free(inj);
        return NULL;
    }
    snprintf(out, n,
        "{\"ok\":true,\"tokens\":%s,\"semantic\":\"Semantic validation successful\",\"injection\":%s,\"ast\":{\"statements\":[%s]}}",
        toks, inj, stmts);
    free(tok_json);
    tok_json = NULL;
    free(g_program_stmts_json);
    g_program_stmts_json = NULL;
    free(inj);
    if (err_out)
        *err_out = NULL;
    return out;
}
