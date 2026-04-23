CREATE DATABASE pa2_test_db;
USE pa2_test_db;
CREATE TABLE Product (pid int, name varchar(20), price float);

-- Insert sample tuples
INSERT INTO Product values (1, 'laptop', 1999.99);
INSERT INTO Product values (2, 'mobile phone', 899.99);
INSERT INTO Product values (3, 'monitor', 1399.99);

-- Query the inserted tuples
SELECT * FROM Product;

-- Modify a tuple
UPDATE Product SET price = 1200.00 WHERE name = 'laptop';

-- Query to verify the modification
SELECT * FROM Product;

-- Delete a tuple
DELETE FROM Product WHERE name = 'monitor';

-- Query to verify the deletion
SELECT * FROM Product;


-- Example output
--
-- Database pa2_test_db created.
-- Using database pa2_test_db.
-- Table Product created.
-- 1 new record inserted.
-- 1 new record inserted.
-- 1 new record inserted.
-- pid int | name varchar(20) | price float
-- 1 | laptop | 1999.99
-- 2 | mobile phone | 899.99
-- 3 | monitor | 1399.99
-- 1 record modified.
-- pid int | name varchar(20) | price float
-- 1 | laptop | 1200.00
-- 2 | mobile phone | 899.99
-- 3 | monitor | 1399.99
-- 1 record deleted.
-- pid int | name varchar(20) | price float
-- 1 | laptop | 1200.00
-- 2 | mobile phone | 899.99