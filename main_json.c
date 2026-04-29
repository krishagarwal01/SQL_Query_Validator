/* stdin -> stdout JSON (for Python subprocess). Build with driver + yacc + flex. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "driver.h"
#include "injection.h"

#define CHUNK 4096

int main(void)
{
    char *buf = NULL;
    size_t cap = 0;
    size_t len = 0;
    int c;

    while ((c = getchar()) != EOF) {
        if (len + 2 > cap) {
            cap = cap ? cap * 2 : CHUNK;
            buf = (char *)realloc(buf, cap);
        }
        buf[len++] = (char)c;
    }
    if (buf)
        buf[len] = '\0';
    else
        buf = strdup("");

    char *err = NULL;
    char *out = parse_sql_to_json(buf, &err);

    if (out) {
        fputs(out, stdout);
        free(out);
        free(buf);
        putchar('\n');
        return 0;
    }
    char *ej = dj_json_string(err ? err : "parse error");
    char *inj = analyze_injection_json(buf ? buf : "");
    printf("{\"ok\":false,\"error\":%s,\"tokens\":[],\"semantic\":\"N/A\",\"injection\":%s,\"ast\":{\"statements\":[]}}\n", ej, inj);
    free(inj);
    free(ej);
    free(err);
    free(buf);
    return 1;
}
