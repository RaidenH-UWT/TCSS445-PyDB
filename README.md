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
START TIMER; /* Starts a timer at the current time */
GET TIMER; /* Prints the current value of the most recently started timer, in seconds */

CREATE DATABASE <name> [path="./"]
DROP DATABASE [IF EXISTS] <name> [path="./"] /* If database is not empty, you will be asked to enter confirmation */
USE <name> [path="./"]

CREATE TABLE <name> <columns>
DROP TABLE <name>
ALTER TABLE <name> <operation> ...
                ADD <columns>
                DROP COLUMN <column>
CREATE INDEX <name> ON <table>(<column>)

SELECT <columns> FROM <table> WHERE <condition>
                    <tables> WHERE <condition>
                    <table> INNER JOIN <table> ON <condition>
                    <table> LEFT OUTER JOIN <table> ON <condition>

LOAD DATA INFILE <csv> INTO TABLE <table>
INSERT INTO <table> [columns] VALUES <values>
UPDATE <table> SET <columns=values> [WHERE <condition>]
DELETE FROM <table> [WHERE <condition>]
```