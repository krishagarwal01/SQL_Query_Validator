#ifndef SEMANTIC_H
#define SEMANTIC_H

const char *schema_table_exists(const char *table);
const char *schema_column_exists(const char *table, const char *column);
int schema_column_count(const char *table);

#endif
