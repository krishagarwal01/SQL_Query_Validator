#ifndef DRIVER_H
#define DRIVER_H

#include <stdarg.h>

void yacc_record_token(int token, const char *yytext);
void yacc_reset_tokens(void);
const char *yacc_tokens_json_finish(void);
char *dj_json_string(const char *raw);
char *dj_aprintf(const char *fmt, ...);
char *parse_sql_to_json(const char *input, char **err_out);

#endif
