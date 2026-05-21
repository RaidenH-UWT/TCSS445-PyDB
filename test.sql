-- Make a new database
CREATE DATABASE db_1;
USE db_1;

-- Make a new table
CREATE TABLE tab (name varchar, age int);
CREATE TABLE tab2 (name varchar, birth int, special varchar);

-- Add data
PRINT Insertion;
INSERT INTO tab VALUES ("abcd", 13), ("efgh", 18), ("ijkl", 32);
INSERT INTO tab2 VALUES ("abcd", 2013, "abcd"), ("efgh", 2008, "ijkl"), ("abcd", 2023, "efgh");

-- Display data
PRINT Selects;
SELECT * FROM tab;
SELECT * FROM tab2;

-- Joins
PRINT Joins;
SELECT * FROM tab, tab2 WHERE tab.name = tab2.name;
SELECT * FROM tab INNER JOIN tab2 ON tab.name = tab2.name;
SELECT * FROM tab LEFT OUTER JOIN tab2 ON tab.name = tab2.name;

-- Alias
-- PRINT Alias;
-- SELECT * FROM tab A, tab2 B
-- WHERE A.name = B.name;

-- SELECT * FROM tab A
-- INNER JOIN tab2 B ON A.name = B.name;

-- Mismatched column names
-- PRINT Mismatched column names;
-- SELECT * FROM tab A, tab2 B
-- WHERE A.name = B.special;
--
-- SELECT * FROM tab A
-- INNER JOIN tab2 B ON A.name = B.special;

-- Cleanup
PRINT Cleanup;
DROP TABLE tab;
DROP TABLE tab2;
DROP DATABASE db_1;