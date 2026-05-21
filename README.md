# TCSS445 PyDB

Python-based simple database management system made for TCSS 445.

Run `pydb.py -h` for usage information

I've disabled all exception raising for the assignment, so the program
will just continue if there's an error. The code for raising exceptions
is still there just commented out.

Supports:
```sql
-- Single line comments
/*
Multiline
    comments
*/
PRINT <text> /* Inline comments */

CREATE DATABASE <name> [path="./"]
DROP DATABASE <name> [path="./"]
USE DATABASE <name> [path="./"]

CREATE TABLE <name> <columns>
DROP TABLE <name>
ALTER TABLE <name> <operation> ...
                   ADD <columns>
                   DROP COLUMN <column>

SELECT <columns> FROM <table> WHERE <condition>
                      <tables> WHERE <condition>
                      <table> INNER JOIN <table> ON <condition>
                      <table> LEFT OUTER JOIN <table> ON <condition>

INSERT INTO <table> [columns] VALUES <values>
UPDATE <table> SET <columns=values> [WHERE <condition>]
DELETE FROM <table> [WHERE <condition>]
```

## Submission

Zip up (into `raidenh_pa3.zip`):

- pydb.py
- output.txt (Output of pydb.py on pa3.sql piped to output.txt)