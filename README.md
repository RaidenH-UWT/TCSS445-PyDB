# TCSS445 PyDB

Python-based simple database management system made for TCSS 445.

Run `pydb.py -h` for usage information

Supports:
```sql
CREATE DATABASE <name> [path="./"]
DROP DATABASE <name> [path="./"]
USE DATABASE <name> [path="./"]

CREATE TABLE <name> <columns>
DROP TABLE <name>
ALTER TABLE <name> <operation> ...
                   ADD <columns>
                   DROP COLUMN <column>

SELECT <columns> FROM <table>
```

## Submission

Zip up (into `raidenh_pa1.zip`):

- pydb.py
- output.txt (Output of pydb.py on pa1.sql piped to output.txt)