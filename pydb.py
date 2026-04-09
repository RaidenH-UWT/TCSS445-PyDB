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
    raw = re.sub(r" +", " ", raw) # cut multiple spaces down to 1
    raw = re.sub(r"--.*", "", raw) # remove comments
    raw = raw.replace("\n", "") # remove newlines
    
    cmds = raw.split(";")[:-1] # split into individual statements
    for cmd in cmds:
        execute(cmd)

def interactive():
    print("""\
    Now running in interactive mode, run a single statement at a time
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
    cmd = cmd.strip()
    if cmd.endswith(";"):
        cmd = cmd[:-1]
    # i just found out about lexical analysis
    # which is absolutely the *correct* tool to do this
    # but i'm going to do it the dumb-but-obvious way:
    # a real big if block
    if cmd[:15].upper() == "CREATE DATABASE":
        create_database(cmd[16:cmd.find(" ", 17) if cmd.find(" ", 17) > -1 else None],
                     cmd[cmd.find(" ", 17):-1] if cmd.find(" ", 17) > -1 else ".")
    elif cmd[:13].upper() == "DROP DATABASE":
        drop_database(cmd[14:cmd.find(" ", 15) if cmd.find(" ", 15) > -1 else None],
                     cmd[cmd.find(" ", 15):-1] if cmd.find(" ", 15) > -1 else ".")
    elif cmd[:3].upper() == "USE":
        # actually simple, just checks if the optional parameter path exists and passes it if so
        use_database(cmd[4:cmd.find(" ", 5) if cmd.find(" ", 5) > -1 else None],
                     cmd[cmd.find(" ", 5):-1] if cmd.find(" ", 5) > -1 else ".")
    elif cmd[:12].upper() == "CREATE TABLE":
        # grab the name, then grab the columns splitting them into a list along commas and then into tuples along spaces
        create_table(cmd[13:cmd.find(" ", 13)],
                     [(col.split(" ")[0], col.split(" ")[1]) for col in cmd[cmd.find(" ", 13) + 2:-1].split(", ")])
    elif cmd[:10].upper() == "DROP TABLE":
        drop_table(cmd[11:])
    elif cmd[:11].upper() == "ALTER TABLE":
        alter_table(cmd[12:cmd.find(" ", 12)], cmd[cmd.find(" ", 12) + 1:])
    elif cmd[:6].upper() == "SELECT":
        # everything between SELECT and FROM, strip the whitespace, and split on commas
        cols = re.sub(r"\s", "", cmd[6:cmd.upper().find("FROM")]).split(",")
        # all that to say: between the FROM and WHERE, or if there's no WHERE then just the end
        table = cmd[cmd.upper().find("FROM") + 5:cmd.upper().find("WHERE") - 1 if cmd.upper().find("WHERE") > -1 else None]
        # all the string after the WHERE, or None if no condition
        cond = cmd[cmd.upper().find("WHERE") + 6:] if cmd.upper().find("WHERE") > -1 else None
        select(cols, table, cond)
    else:
        # raise SyntaxError(f"ERROR: Command {cmd} could not be parsed")
        print(f"ERROR: Command {cmd} could not be parsed")

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
            print(f"Created table {name}")
    
def drop_table(name):
    """Delete tables.
    
    Arguments:
    name -- Name of the table to delete.
    
    Raises:
    FileNotFoundError if the given does not lead to a table.
    RuntimeError if there is no database being used.
    """
    path = os.path.join(current_database, name)
    if current_database == "":
        # raise RuntimeError("ERROR: No database in use")
        print("ERROR: No database in use")
    else:
        try:
            os.remove(path)
            print(f"Dropped table {name}")
        except FileNotFoundError:
            # raise FileNotFoundError(f"ERROR: Table {path} does not exist.")
            print(f"ERROR: Table {name} does not exist.")

def alter_table(name, cmd):
    """Alter table metadata.
    
    Arguments:
    name -- String name of the table to modify.
    cmd -- String alteration to perform.
    
    Raises:
    FileNotFoundError if the given name does not lead to a table.
    RuntimeError if there is no database being used.
    SyntaxError if cmd uses invalid syntax
    """
    if current_database == "":
        # raise RuntimeError("ERROR: No database in use")
        print("ERROR: No database in use")
    else:
        try:
            with open(os.path.join(current_database, name), "r") as inFile:
                lines = inFile.readlines()
            if cmd[:3].upper() == "ADD":
                print(f"Adding column {cmd[4:]} to table {name}")
                lines[0] += f"|{cmd[4:]}"
                for i in range(len(lines) - 1):
                    lines[i + 1] = lines[i + 1] + '|""'
            elif cmd[:11].upper() == "DROP COLUMN":
                column = cmd[12:]
                
                print(f"Dropping column {column} from table {name}")
                
                if column in [col[:col.find(" ")] for col in lines[0].split("|")]:
                    index = [col[:col.find(" ")] for col in lines[0].split("|")].index(column)
                    heads = lines[0].split("|")
                    heads.pop(index)
                    lines[0] = "|".join(heads) + "\n"
                    for i in range(len(lines) - 1):
                        values = lines[i + 1].split(r'"|"')
                        values.pop(index)
                        lines[i + 1] = r'"|"'.join(values) + '"\n'
                    # trim the trailing newline
                    lines[-1] = lines[-1][:-1]
                else:
                    # raise SyntaxError(f"ERROR: Column {column} not in table {name}")
                    print(f"ERROR: Column {column} not in table {name}")
                    return
            with open(os.path.join(current_database, name), "w") as outFile:
                outFile.writelines(lines)
        except FileNotFoundError:
            print(f"ERROR: Table {name} does not exist.")

def select(columns, table, condition = None):
    """Select data from a table.
    
    Arguments:
    columns -- Which columns to select. Either list of string column names, or "*" for all columns.
    table -- Which table to select from.
    condition -- Conditions to select data on (default is None)
    
    Raises:
    FileNotFoundError if the given table does not lead to a table.
    RuntimeError if there is no database being used.
    """
    if current_database == "":
        # raise RuntimeError("ERROR: No database in use")
        print("ERROR: No database in use")
    else:
        path = os.path.join(current_database, table)
        if not os.path.exists(path):
            # raise FileNotFoundError(f"ERROR: Table {table} does not exist")
            print(f"ERROR: Table {table} does not exist")
            return
        data = ""
        with open(path, "r") as reader:
            data = reader.read()
        # split up the data by its separators
        lines = data.split("\n")
        lines[0] = lines[0].split("|")
        for i in range(len(lines) - 1):
            # Little check to handle blank lines in tables
            # - shouldn't happen in program-generated tables
            # but it messed me up in testing so it gets some validation
            if lines[i + 1] == "":
                lines.pop(i + 1)
                continue
            
            # Split at quoted pipes
            lines[i + 1] = re.split(r'"\|"', lines[i + 1])
            # trim quotes the regex missed
            lines[i + 1][0] = lines[i + 1][0][1:]
            lines[i + 1][-1] = lines[i + 1][-1][:-1]
        
        indexes = []
        widths = {}
        
        # Select columns
        for header in lines[0]:
            # If the header name we're looking at is in columns, grab it
            if header[:header.find(" ")] in columns or columns[0] == "*":
                # Append the index of the column
                indexes.append(lines[0].index(header))
                # Find the widest element in the column and save its width
                widths[indexes[-1]] = max([len(x[indexes[-1]]) for x in lines])
        
        # Maybe add a nice lil note about the number of records retrieved here? tough if
        # i'm checking the condition in the drawing
        print(f"Selecting {columns} from {table}")
        # Print pretty boxes!
        for line in lines:
            # TODO: Check condition in here
            for i in range(len(indexes)):
                print(f"+{'-' * (widths[indexes[i]] + 2)}", end = "")
            print("+")
            for i in range(len(indexes)):
                print(f"|{line[indexes[i]].center(widths[i] + 2)}", end = "")
            print("|")
        # Last line
        for i in range(len(indexes)):
            print(f"+{'-' * (widths[indexes[i]] + 2)}", end = "")
        print("+")

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
    # TODO: Datatype validation implementation
    return True

def test():
    """Testing"""
    execute("USE DATABASE db_0")

if __name__ == "__main__":
    main()