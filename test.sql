-- Make a new database
CREATE DATABASE db_1;
USE db_1;

-- Make a new table
CREATE TABLE tab (id int, name varchar, age int);
CREATE TABLE tab2 (num int, str varchar);

-- Add data
PRINT Insertion;
INSERT INTO tab VALUES
    (1, "a", 13),
    (2, "b", 24),
    (3, "c", 78),
    (4, "d", 82),
    (5, "e", 29),
    (6, "f", 92);

INSERT INTO tab2 VALUES
    (17, "a"),
    (178, "b")

PRINT Make index;
CREATE INDEX age_idx ON tab(age);

PRINT Selections;
SELECT * FROM tab;
SELECT * FROM tab WHERE age = 24;
SELECT * FROM tab WHERE age < 78;
SELECT * FROM tab WHERE age > 29;
SELECT * FROM tab WHERE age > 24 AND age < 82;
SELECT * FROM tab O, tab2 T WHERE O.name = T.str;

-- Cleanup
PRINT Cleanup;
DROP TABLE tab;
DROP TABLE tab2;
DROP DATABASE db_1;