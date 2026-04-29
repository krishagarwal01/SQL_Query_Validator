#include "semantic.h"
#include <string.h>

typedef struct {
    const char *name;
    const char *columns[8];
    int count;
} SchemaDef;

static const SchemaDef SCHEMA[] = {
    {"students", {"id", "name", "age", "course_id"}, 4},
    {"courses", {"id", "title"}, 2},
    {"teachers", {"id", "name", "subject"}, 3},
};

static const int SCHEMA_COUNT = (int)(sizeof(SCHEMA) / sizeof(SCHEMA[0]));

static const SchemaDef *find_table(const char *table)
{
    int i;
    if (!table) {
        return NULL;
    }
    for (i = 0; i < SCHEMA_COUNT; i++) {
        if (strcmp(SCHEMA[i].name, table) == 0) {
            return &SCHEMA[i];
        }
    }
    return NULL;
}

const char *schema_table_exists(const char *table)
{
    return find_table(table) ? table : NULL;
}

const char *schema_column_exists(const char *table, const char *column)
{
    const SchemaDef *t = find_table(table);
    int i;
    if (!t || !column) {
        return NULL;
    }
    for (i = 0; i < t->count; i++) {
        if (strcmp(t->columns[i], column) == 0) {
            return column;
        }
    }
    return NULL;
}

int schema_column_count(const char *table)
{
    const SchemaDef *t = find_table(table);
    if (!t) {
        return -1;
    }
    return t->count;
}
