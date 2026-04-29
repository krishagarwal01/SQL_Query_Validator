/* Flex lexer — token hooks for JSON + Yacc tokens */
%{
#include "sql.tab.h"
#include "driver.h"
#include <stdlib.h>
#include <string.h>
%}
%option nounput
%option noyywrap

%%

[ \t\r]+
\n

">="    { yacc_record_token(GE, yytext); return GE; }
"<="    { yacc_record_token(LE, yytext); return LE; }
"!="    { yacc_record_token(NE, yytext); return NE; }
"="     { yacc_record_token(EQ, yytext); return EQ; }
">"     { yacc_record_token(GT, yytext); return GT; }
"<"     { yacc_record_token(LT, yytext); return LT; }

","     { yacc_record_token(COMMA, yytext); return COMMA; }
";"     { yacc_record_token(SEMICOLON, yytext); return SEMICOLON; }
"("     { yacc_record_token(LPAREN, yytext); return LPAREN; }
")"     { yacc_record_token(RPAREN, yytext); return RPAREN; }
"*"     { yacc_record_token(STAR, yytext); return STAR; }

SELECT   { yacc_record_token(SELECT, yytext); return SELECT; }
FROM     { yacc_record_token(FROM, yytext); return FROM; }
WHERE    { yacc_record_token(WHERE, yytext); return WHERE; }
INSERT   { yacc_record_token(INSERT, yytext); return INSERT; }
INTO     { yacc_record_token(INTO, yytext); return INTO; }
VALUES   { yacc_record_token(VALUES, yytext); return VALUES; }
UPDATE   { yacc_record_token(UPDATE, yytext); return UPDATE; }
SET      { yacc_record_token(SET, yytext); return SET; }
DELETE   { yacc_record_token(DELETE, yytext); return DELETE; }

[0-9]+ {
    yylval.str = strdup(yytext);
    yacc_record_token(NUMBER, yytext);
    return NUMBER;
}

'[^'\n]*' {
    yylval.str = strdup(yytext);
    yacc_record_token(STRING, yytext);
    return STRING;
}

[A-Za-z_][A-Za-z0-9_]* {
    yylval.str = strdup(yytext);
    yacc_record_token(IDENTIFIER, yytext);
    return IDENTIFIER;
}

. {
    fprintf(stderr, "Illegal character: %s\n", yytext);
    exit(1);
}

%%
