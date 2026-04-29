#include "injection.h"
#include "driver.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    const char *needle;
    const char *message;
    const char *risk;
    int level_num;
} Pattern;

static const Pattern PATTERNS[] = {
    {"or '1'='1'", "Tautology: OR '1'='1'", "critical", 3},
    {"union select", "UNION-based injection (UNION SELECT)", "critical", 3},
    {";drop", "Stacked command after semicolon", "critical", 3},
    {";truncate", "Stacked command after semicolon", "critical", 3},
    {";alter", "Stacked command after semicolon", "critical", 3},
    {";create", "Stacked command after semicolon", "critical", 3},
    {"exec(", "Execute / exec-style payload", "critical", 3},
    {" xp_", "Extended stored procedure (xp_*)", "high", 2},
    {"sleep(", "Time-based blind SQL patterns", "high", 2},
    {"benchmark(", "Time-based blind SQL patterns", "high", 2},
    {"waitfor delay", "Time-based blind SQL patterns", "high", 2},
    {"into outfile", "File read / write patterns", "high", 2},
    {"load_file(", "File read / write patterns", "high", 2},
    {"/*", "Block comment (often used to bypass filters)", "medium", 1},
    {"--", "Line comment in expression", "medium", 1},
    {"#", "Line comment in expression", "medium", 1},
    {"information_schema", "Metadata catalog access", "medium", 1},
    {"pg_catalog", "Metadata catalog access", "medium", 1},
    {"char(", "CHAR() concatenation (obfuscation)", "medium", 1},
    {"concat(", "String concatenation / hex literals", "low", 0},
    {"0x", "String concatenation / hex literals", "low", 0},
};

static const int PATTERN_COUNT = (int)(sizeof(PATTERNS) / sizeof(PATTERNS[0]));

static char *to_lower_copy(const char *s)
{
    size_t i;
    size_t n = strlen(s);
    char *out = (char *)malloc(n + 1);
    if (!out) {
        return strdup("");
    }
    for (i = 0; i < n; i++) {
        char c = s[i];
        if (c >= 'A' && c <= 'Z') {
            out[i] = (char)(c - 'A' + 'a');
        } else {
            out[i] = c;
        }
    }
    out[n] = '\0';
    return out;
}

static char *json_escape_snippet(const char *s, size_t pos)
{
    size_t max_len = 120;
    size_t remain = strlen(s + pos);
    size_t len = remain > max_len ? max_len : remain;
    char temp[128];
    snprintf(temp, sizeof(temp), "%.*s%s", (int)len, s + pos, remain > max_len ? "..." : "");
    return dj_json_string(temp);
}

char *analyze_injection_json(const char *sql)
{
    int i;
    int highest = 0;
    int first = 1;
    char *lower;
    char *findings = strdup("[");
    if (!sql || !sql[0]) {
        return strdup("{\"level\":\"low\",\"level_num\":0,\"findings\":[]}");
    }
    lower = to_lower_copy(sql);

    for (i = 0; i < PATTERN_COUNT; i++) {
        char *hit = strstr(lower, PATTERNS[i].needle);
        if (hit) {
            size_t idx = (size_t)(hit - lower);
            char *snippet = json_escape_snippet(sql, idx);
            char *pattern_json = dj_json_string(PATTERNS[i].needle);
            char *message_json = dj_json_string(PATTERNS[i].message);
            char *entry = dj_aprintf(
                "%s{\"pattern\":%s,\"message\":%s,\"risk\":\"%s\",\"snippet\":%s}",
                first ? "" : ",",
                pattern_json,
                message_json,
                PATTERNS[i].risk,
                snippet);
            char *merged = dj_aprintf("%s%s", findings, entry);
            free(findings);
            findings = merged;
            free(entry);
            free(snippet);
            free(pattern_json);
            free(message_json);
            first = 0;
            if (PATTERNS[i].level_num > highest) {
                highest = PATTERNS[i].level_num;
            }
        }
    }

    {
        const char *level = "low";
        char *final_json;
        char *closed = dj_aprintf("%s]", findings);
        free(findings);
        if (highest == 1) {
            level = "medium";
        } else if (highest == 2) {
            level = "high";
        } else if (highest == 3) {
            level = "critical";
        }
        final_json = dj_aprintf("{\"level\":\"%s\",\"level_num\":%d,\"findings\":%s}", level, highest, closed);
        free(closed);
        free(lower);
        return final_json;
    }
}
