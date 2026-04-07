#! /bin/python
"""Python-based database management system.

Author: Raiden H
Updated: 26-04-06

Usage:  
    pydb -h
    pydb <FILE> [-q]
    pydb -s "<SQL>" [-q]
    pydb -i

Options:
    -h          Prints this help message
    [file]      Executes the statements of a .sql file
    -s "<SQL>"  Executes the passed SQL statements. Requires quotes.
    -i          Runs in interactive mode, letting the user enter statements one at a time
    -q          Runs in quiet mode, not printing any output except errors.

SQL Support:
    CREATE DATABASE <name> [path="./"]
    DROP DATABASE <name> [path="./"]
    USE DATABASE <name> [path="./"]

    CREATE TABLE <name> <columns>
    DROP TABLE <name>
    ALTER TABLE <name> <operation> ...
                       ADD <columns>
                       DROP COLUMN <column>

    SELECT <columns> FROM <table>
"""

import os
import re
import sys

PRINT_INFO = True
current_database = ""

def main():
    """Handle input and pass it off to helper functions."""
    PRINT_INFO = "-q" not in sys.argv
    raw = ""
    if sys.argv[1] == "-h":
        print(__doc__)
        return
    elif sys.argv[1] == "-t":
        test()
        return
    elif sys.argv[1] == "-s":
        raw = sys.argv[2]
    elif sys.argv[1].endswith(".sql"):
        with open(sys.argv[1], "r") as file:
            raw = file.read()
    elif sys.argv[1] == "-i":
        interactive()
    else:
        print("Bad arguments")
        print(__doc__)
        return

    # Now we've got long input, time to tokenize it
    raw = re.sub(" +", " ", raw) # cut multiple spaces down to 1
    raw = re.sub("--.*", "", raw) # remove comments
    raw = raw.replace("\n", "") # remove newlines
    
    cmds = raw.split(";")[:-1] # split into individual statements
    print(cmds)
    for cmd in cmds:
        execute(cmd)

def interactive():
    print("""\
Now running in interactive mode
Interrupt or type 'exit' to exit
Type '\\c' to clear the current statement\
""")
    while True:
        print("> ", end = "")
        try:
            cmd = input()
            if cmd == "exit":
                print("Exiting")
                return
            elif cmd.endswith("\\c"):
                print("Cleared")
                continue
            execute(cmd)
        except KeyboardInterrupt:
            return

def execute(cmd):
    """Parse and execute SQL statement.
    
    Arguments:
    cmd -- Single SQL statement to parse
    
    Raises:
    SyntaxError if the statement cannot be parsed.
    """
    if cmd.endswith(";"):
        cmd = cmd[:-1]
    print("Executing: " + cmd)

def create_database(name, path = "."):
    """Create databases.
    
    Arguments:
    name -- Name of the database to create
    path -- Filepath to a directory to put the database (default is the current directory)
    
    Raises:
    FileExistsError if the given name and path lead to an already existing database.
    """
    full_path = os.path.abspath(os.path.join(os.path.expanduser(path), name))
    try:
        os.mkdir(full_path)
        if PRINT_INFO:
            print(f"Created database {name} at {os.path.join(path, name)}")
    except FileExistsError:
        # raise FileExistsError(f"ERROR: Database {full_path} already exists.")
        print(f"ERROR: Database {full_path} already exists.")

def drop_database(name, path = "."):
    """Delete databases.
    
    Arguments:
    name -- Name of the database to delete
    path -- Filepath to a directory where the database is (default is the current directory)
    
    Raises:
    FileNotFoundError if the given name and path do not lead to a database.
    """
    full_path = os.path.abspath(os.path.join(os.path.expanduser(path), name))
    try:
        os.rmdir(full_path)
        if PRINT_INFO:
            print(f"Deleted database {name} at {os.path.join(path, name)}")
    except FileNotFoundError:
        # raise FileNotFoundError(f"ERROR: Directory {full_path} does not exist.")
        print(f"ERROR: Directory {full_path} does not exist.")
    
def use_database(name, path = "."):
    """Select databases.
    
    Arguments:
    name -- Name of the database to select
    path -- Filepath to a directory where the database is (default is the current directory)
    
    Raises:
    FileNotFoundError if the given name and path do not lead to a database.
    """
    full_path = os.path.abspath(os.path.join(os.path.expanduser(path), name))
    exists = os.path.exists(full_path)
    if not exists:
        # raise FileNotFoundError(f"ERROR: Directory {full_path} does not exist")
        print(f"ERROR: Directory {full_path} does not exist")
    else:
        global current_database
        current_database = full_path
        if PRINT_INFO:
            print(f"Using database {os.path.join(path, name)}")
    
def create_table(name, columns):
    """Create tables.
    
    Arguments:
    name -- String name of the table to create
    columns -- List of tuple columns of the table like [(name, type), ...]
    
    Raises:
    FileExistsError if the given name and path lead to an already existing table.
    RuntimeError if there is no database being used.
    SyntaxError if the columns use illegal datatypes
    """
    path = os.path.join(current_database, name)
    if current_database == "":
        # raise RuntimeError("ERROR: No database in use")
        print("ERROR: No database in use")
    elif os.path.exists(path):
        # raise FileExistsError(f"ERROR: Table {path} already exists")
        print(f"ERROR: Table {path} already exists")
    else:
        for col in columns:
            if not validate_datatype(col[1]):
                # raise SyntaxError(f"ERROR: Column: {col} has illegal datatype")
                print(f"ERROR: Column: {col} has illegal datatype")
        with open(path, "w") as table:
            table.write("|".join([f"{col[0]} {col[1]}" for col in columns]))
    
def drop_table(name):
    """Delete tables.
    
    Arguments:
    name -- Name of the table to delete.
    
    Raises:
    FileNotFoundError if the given does not lead to a table.
    RuntimeError if there is no database being used.
    """

def alter_table(name, cmd):
    """Alter table metadata.
    
    Arguments:
    name -- Name of the table to modify.
    cmd -- Alteration to perform.
    
    Raises:
    FileNotFoundError if the given name does not lead to a table.
    RuntimeError if there is no database being used.
    """

def select(columns, table, condition = None):
    """Select data from a table.
    
    Arguments:
    columns -- Which columns to select.
    table -- Which table to select from.
    condition -- Conditions to select data on (default is None)
    
    Raises:
    FileNotFoundError if the given table does not lead to a table.
    RuntimeError if there is no database being used.
    """

def validate_datatype(datatype):
    """Validate a given SQL datatype.
    
    Arguments:
    datatype -- a string representing a SQL datatype.
    
    Returns:
    True if the datatype is a valid SQL datatype, false otherwise.
    """
    
    """
    Legal types (i just picked some out):
    CHAR(size) 0 <= size <= 255 = 1
    VARCHAR(size) 0 <= size <= 65535
    BOOL 0 / 1
    BOOLEAN same ^
    INT(size) 0 <= size <= 255 (min display size)
    INTEGER(size) same ^
    DEC(size, d) 0 <= size <= 65 = 10, 0 <= d <= 30 = 0
    DECIMAL(size, d) same ^
    FLOAT(p) 0 <= p <= 53
    DATE YYYY-MM-DD
    DATETIME YYYY-MM-DD hh:mm:ss
    """
    return True

def test():
    """Testing"""
    # drop_database("db_0")
    create_database("db_0")
    use_database("db_0")
    create_table("tab", [("name", "varchar(128)"), ("age", "int")])

if __name__ == "__main__":
    main()