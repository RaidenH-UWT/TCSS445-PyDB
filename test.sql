-- Make a new database
CREATE DATABASE db_1;
USE db_1;

-- Make a new table
CREATE TABLE tab (name varchar, age int);
CREATE TABLE tab2 (name varchar, birth int);

-- Add data
INSERT INTO tab VALUES ("abcd", 13), ("efgh", 18), ("ijkl", 32);
INSERT INTO tab2 VALUES ("abcd", 2013), ("efgh", 2008);

-- Display data
SELECT * FROM tab;
SELECT * FROM tab2;

-- Joins
SELECT * FROM tab, tab2 WHERE tab.name = tab2.name;
SELECT * FROM tab INNER JOIN tab2 ON tab.name = tab2.name;
SELECT * FROM tab LEFT OUTER JOIN tab2 ON tab.name = tab2.name;

-- Cleanup
DROP TABLE tab;
DROP TABLE tab2;
DROP DATABASE db_1;