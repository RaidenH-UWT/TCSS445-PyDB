-- Make a new database
CREATE DATABASE db_1;
USE db_1;

-- Make a new table
CREATE TABLE tab (text varchar, num int);

-- Add data
INSERT INTO tab VALUES ("ASDF", 1);
INSERT INTO tab VALUES ("A", 1), ("B", 2), ("C", 3);

-- Display data
SELECT * FROM tab;
SELECT * FROM tab WHERE num=1;

-- Alter table
ALTER TABLE tab ADD num2 float

-- Cleanup
DROP TABLE tab;
DROP DATABASE db_1;