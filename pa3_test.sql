CREATE DATABASE TCSS455_PA3;
USE TCSS455_PA3;

CREATE TABLE Employee (
    id INT,
    name VARCHAR(10)
);

CREATE TABLE Sales (
    employeeID INT,
    productID INT
);

INSERT INTO Employee (id, name) VALUES (1, 'Joe');
INSERT INTO Employee (id, name) VALUES (2, 'Jack');
INSERT INTO Employee (id, name) VALUES (3, 'Gill');

INSERT INTO Sales (employeeID, productID) VALUES (1, 344);
INSERT INTO Sales (employeeID, productID) VALUES (1, 355);
INSERT INTO Sales (employeeID, productID) VALUES (2, 544);

/* Implicit Inner Join */
SELECT * FROM Employee E, Sales S 
WHERE E.id = S.employeeID;

/* Explicit Inner Join */
SELECT * FROM Employee E 
INNER JOIN Sales S ON E.id = S.employeeID;

/* The following will include Gill */
SELECT * FROM Employee E 
LEFT OUTER JOIN Sales S ON E.id = S.employeeID;

-- Expected output
--
-- Database TCSS455_PA3 created.
-- Using database TCSS455_PA3.
-- Table Employee created.
-- Table Sales created.
-- 1 new record inserted.
-- 1 new record inserted.
-- 1 new record inserted.
-- 1 new record inserted.
-- 1 new record inserted.
-- 1 new record inserted.
-- id INT|name VARCHAR(10)|employeeID INT|productID INT
-- 1|Joe|1|344
-- 1|Joe|1|355
-- 2|Jack|2|544
-- id INT|name VARCHAR(10)|employeeID INT|productID INT
-- 1|Joe|1|344
-- 1|Joe|1|355
-- 2|Jack|2|544
-- id INT|name VARCHAR(10)|employeeID INT|productID INT
-- 1|Joe|1|344
-- 1|Joe|1|355
-- 2|Jack|2|544
-- 3|Gill||