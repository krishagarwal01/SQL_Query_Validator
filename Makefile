# Flex + Bison + C driver (JSON bridge for Python UI)
# Windows: use MSYS2, WSL, or WinFlexBison; then: mingw32-make

BISON = bison
FLEX  = flex
CC    = gcc

all: sqlparse_json sqlparse_json.exe

sql.tab.c sql.tab.h: sql.y
	$(BISON) -d sql.y

lex.yy.c: sql.l sql.tab.h
	$(FLEX) sql.l

sqlparse_json: sql.tab.c lex.yy.c driver.c semantic.c injection.c main_json.c
	$(CC) -O2 -o $@ sql.tab.c lex.yy.c driver.c semantic.c injection.c main_json.c

sqlparse_json.exe: sql.tab.c lex.yy.c driver.c semantic.c injection.c main_json.c
	$(CC) -O2 -o $@ sql.tab.c lex.yy.c driver.c semantic.c injection.c main_json.c

clean:
	rm -f sql.tab.c sql.tab.h lex.yy.c sqlparse_json sqlparse_json.exe

.PHONY: all clean
