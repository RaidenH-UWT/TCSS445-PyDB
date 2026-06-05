#! /bin/python
"""Python-based database management system.

Author: Raiden H
Updated: 26-06-04

Usage:
    pydb -h
    pydb <FILE> [-q]
    pydb -s "<SQL>" [-q]
    pydb -i [-q]

Options:
    -h          Prints this help message
    <FILE>      Executes the statements of a .sql file
    -s "<SQL>"  Executes the passed SQL statements. Requires quotes.
    -i          Runs in interactive mode, letting the user enter statements one at a time
    -q          Runs in quiet mode, not printing any output except errors.

SQL Support:
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
"""

import csv
import os
import re
import shutil
import sys
import time

PRINT_INFO = True
current_database = ""
indexes = {}
current_time = 0

class BPlusTree:
    """B+ tree implementation for efficient selections. Values should be list records.

    Arguments:
    degree -- degree (minimum # child nodes, 1/2 maximum) of the B+ tree
    """
    def __init__(self, degree):
        self.degree = degree
        self.root = self.Node(self.degree)
        self.root.parent = self
    
    def __str__(self):
        return f"BPlusTree (degree {self.degree}): \n{self.root}"
        
    def _search(self, value):
        """Internal search implementation. Always returns a node.
        
        Arguments:
        value -- Value to search for.
        
        Returns:
        node -- Node the value is located in, or would be located in, whether or not the value is in the node.
        """
        leaf = self.root
        while not leaf.is_leaf():
            if value == None:
                if leaf.values[0] and type(leaf.values[0]) == BPlusTree.Node:
                    temp = leaf.values[0]
                else:
                    break
            else:
                n = len(leaf.keys) + 1
                for i in range(n):
                    temp = leaf.values[i]
                    if i == len(leaf.keys):
                        temp = leaf.values[i]
                        break
                    if leaf.keys[i] > value:
                        break
                
            leaf = temp
        return leaf
    
    def search(self, key):
        """Search the tree for a key.
        
        Arguments:
        key -- Key to search for.
        
        Returns:
        (Node, index) -- If key is found in the tree.
        None -- If key is not in the tree.
        """
        node = self._search(key)
        out = []
        while True:
            for i in range(len(node.keys)):
                if node.keys[i] == key:
                    if type(node.values[i][0]) == list:
                        out.extend(node.values[i])
                    else:
                        out.append(node.values[i])
            if node.next:
                node = node.next
            else:
                return out
    
    def search_range(self, start = None, end = None):
        """Search the tree for a range of values.
        
        Arguments:
        start -- Start of range (exclusive). Optional.
        end -- End of range (exclusive). Optional.
        
        Returns:
        value[] -- List of values inside the range in ascending order.
        """
        node = self._search(start)
        out = []
        while True:
            for i in range(len(node.keys)):
                if not end or node.keys[i] < end:
                    if not start or node.keys[i] > start:
                        if type(node.values[i][0]) == list:
                            out.extend(node.values[i])
                        else:
                            out.append(node.values[i])
                else:
                    return out
            if node.next:
                node = node.next
            else:
                return out

    def insert(self, value, key = None):
        """Insert a value into the BPlusTree.
        
        Arguments:
        value -- Value to insert into the tree. Must be of a comparable type if key is not provided.
        value -- Key to insert into the tree. Must be of a comparable type. Optional.
        """
        if key:
            target = self._search(key)
            target.insert(key, value)
        else:
            target = self._search(value)
            target.insert(value, value)         
    
    def delete(self, value):
        """Delete a value from the BPlusTree.
        
        Arguments:
        value -- Value to delete from the tree.
        """
        target = self._search(value)
        if value in target.values:
            target.delete(value)

    class Node:
        """Single Node of the BPlusTree.
        
        Arguments:
        degree -- Degree of the Node. Must match the BPlusTree the Node is a part of.
        keys -- List of keys. Keys may be of any comparable type.
        values -- List of values. May either be the same type as the keys, or Nodes themselves.
        parent -- Parent Node of this Node.
        """
        def __init__(self, degree, keys = [], values = [], parent = None):
            self.degree = degree
            self.keys = keys
            self.values = values
            self.parent = parent
            self.next = None
            self.prev = None
        
        def __str__(self):
            return f'  Node (leaf: {self.is_leaf()})  Keys: {self.keys}  Values: [{'\n' + '\n'.join([str(val) for val in self.values]) if isinstance(self.values[0] if len(self.values) > 0 else "[]", BPlusTree.Node) else ' '.join([str(val) for val in self.values])}]'
        
        def is_leaf(self):
            """Returns True if this Node is a leaf, False otherwise.
            """
            return len(self.values) == 0 or not isinstance(self.values[0], BPlusTree.Node)
        
        def insert(self, key, value):
            """Insert a key/value pair into the node, splitting if necessary.
            
            Arguments:
            key -- Key to insert. May be of any comparable type.
            value -- Value to insert. May either be the same type as the key, or a Node itself.
            """
            index = ([x for x in range(len(self.keys)) if self.keys[x] < key] or [-1])[-1]
            if key not in self.keys:
                self.keys.insert(index + 1, key)
                self.values.insert(index + 1 + (type(value) == BPlusTree.Node), value)
                if len(self.keys) > 2 * self.degree:
                    self.split()
            else:
                index += 1
                if type(self.values[index][0]) == list:
                    self.values[index] = self.values[index] + [value]
                else:
                    self.values[index] = [self.values[index]] + [value]
            
        def split(self):
            """Split the node into two nodes and shift the center element to the parent.
            """
            mid = len(self.keys) // 2
            new = BPlusTree.Node(self.degree, self.keys[mid:], self.values[mid:], self.parent)
            new.next = self.next
            new.prev = self
            if self.next:
                self.next.prev = new
            
            # Special case for root; need to keep the tree root pointing to the right spot
            if type(self.parent) == BPlusTree:
                tree = self.parent
                self.parent = BPlusTree.Node(self.degree, [], [self], tree)
                tree.root = self.parent
                new.parent = self.parent
            self.parent.insert(self.keys[mid], new)
            self.keys = self.keys[:mid]
            self.values = self.values[:mid]
            self.next = new
            
        def delete(self, value):
            """Delete a value from the tree, merging nodes if necessary.
            
            Arguments:
            value -- Value to delete. May either be the same type as the key, or a Node itself.
            """
            self.values.remove(value)
            if type(value) != BPlusTree.Node:
                self.keys.remove(value)
            if len(self.values) < self.degree:
                if len(self.prev.values) > self.degree:
                    self.values.insert(0, self.prev.values.pop())
                    self.keys.insert(0, self.prev.keys.pop())
                    self.parent.keys[0] = self.keys[0]
                elif len(self.next.values) > self.degree:
                    self.values.append(self.next.values.pop(0))
                    self.keys.append(self.next.keys.pop(0))
                    self.parent.keys[-1] = self.keys[-1]
                else:
                    self.merge()
            
        def merge(self):
            """Merge the node with one of it's neighbors (preferring previous).
            """
            # Select the node to merge with. Doesn't matter but prefers previous node.
            if len(self.prev.values) + len(self.values) < 2 * self.degree:
                self.prev.parent.keys.pop(self.prev.parent.values.index(self.prev))
                self.keys = self.prev.keys + self.keys
                self.values = self.prev.values + self.values
                self.prev.prev.next = self
                self.prev.parent.delete(self.prev)
            else:
                self.parent.keys.pop(self.parent.values.index(self))
                self.keys = self.keys + self.next.keys
                self.values = self.values + self.next.values
                self.next.next.prev = self
                self.next.parent.delete(self.next)

def main():
    """Handle input and pass it off to helper functions.
    """
    global PRINT_INFO
    PRINT_INFO = "-q" not in sys.argv
    raw = ""
    if len(sys.argv) == 1 or sys.argv[1] == "-h":
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
        _interactive()
    else:
        print("Bad arguments")
        print(__doc__)
        return

    # Now we've got long input, time to tokenize it
    raw = re.sub(r" {2,}", "", raw) # cut multiple spaces
    raw = re.sub(r"--.*", "", raw) # remove full-line comments
    raw = re.sub(r"/\*[\S\s]*?\*/", "", raw) # remove inline comments
    raw = raw.replace("\n", "") # remove newlines
    raw = re.sub(r"(\S),(\S)", r"\1, \2", raw) # put a space back after commas

    cmds = raw.split(";")[:-1] # split into individual statements
    for cmd in cmds:
        execute(cmd)

def _interactive():
    """Runs the program in interactive mode, rather than from argument or file SQL.
    """
    print("""\
    Now running in interactive mode, enter a single statement at a time
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
            print()
            return

def execute(cmd):
    """Parse and execute SQL statement.

    Arguments:
    cmd -- Single SQL statement to parse

    Raises:
    SyntaxError if the statement cannot be parsed.
    """
    global PRINT_INFO
    global current_time
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
        if "IF EXISTS" in cmd:
            drop_database(cmd[24:cmd.find(" ", 25) if cmd.find(" ", 25) > -1 else None],
                     cmd[cmd.find(" ", 25):-1] if cmd.find(" ", 25) > -1 else ".", True)
        else:
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
    elif cmd[:12].upper() == "CREATE INDEX":
        create_index(cmd[13:cmd.find(" ", 13)], cmd[cmd.upper().find("ON") + 3:cmd.find("(")].strip(), cmd[cmd.find("(") + 1:-1])
    elif cmd[:16].upper() == "LOAD DATA INFILE":
        load_csv(cmd[17:cmd.find(" ", 17)].strip().replace("'", "").replace('"', ""), cmd[cmd.rfind(" ") + 1:])
    elif cmd[:6].upper() == "SELECT":
        # everything between SELECT and FROM, strip the whitespace, and split on commas
        cols = re.sub(r"\s", "", cmd[6:cmd.upper().find("FROM")]).split(",")
        # all that to say: between the FROM and WHERE, or if there's no WHERE then just the end
        table = cmd[cmd.upper().find("FROM") + 5:cmd.upper().find("WHERE") - 1 if cmd.upper().find("WHERE") > -1 else None]
        # all the string after the WHERE, or None if no condition
        if 'ON' in cmd.upper():
            cond = cmd[cmd.upper().find("ON") + 3:].strip()
        else:
            cond = cmd[cmd.upper().find("WHERE") + 6:].strip() if "WHERE" in cmd.upper() else None
        # transform cond into a dict
        structCond = {}
        if not cond == None:
            cond = re.split(" and ", cond, flags=re.IGNORECASE)
            for c in cond:
                if c[:c.find(" ")] in structCond:
                    structCond[c[:c.find(" ")]].append({"comp": c[c.find(" ") + 1:c.find(" ", c.find(" ") + 1)], "value": c[c.rfind(" ") + 1:].replace("'", "").replace('"', '')})
                else:
                    structCond[c[:c.find(" ")]] = [{"comp": c[c.find(" ") + 1:c.find(" ", c.find(" ") + 1)], "value": c[c.rfind(" ") + 1:].replace("'", "").replace('"', '')}]
        print_table(select(cols, table, structCond))
    elif cmd[:11].upper() == "INSERT INTO":
        if cmd[cmd.find("VALUES") + 6] != " ":
            cmd = cmd[:cmd.find("VALUES") + 6] + " " + cmd[cmd.find("VALUES") + 6:]
        table = cmd[12:cmd.find(" ", 12)]
        columns = cmd[cmd.find(table) + len(table) + 2:cmd.upper().find("VALUES") - 2].strip()
        values = re.split(r'\),\s*\(', cmd[cmd.upper().find('VALUES') + 8:-1])
        # transform values into list of lists
        insert(table, [[re.sub(r'[\'"]', '', x).strip() for x in val.split(',')] for val in values], None if len(columns) == 0 else columns.replace(' ', '').split(','))
    elif cmd[:6].upper() == "UPDATE":
        table = cmd[7:cmd.find(" ", 7)]
        records = cmd[cmd.upper().find("SET") + 4:cmd.upper().find("WHERE") - 1 if cmd.upper().find("WHERE") > -1 else None]
        records = [x.strip() for x in records.split(',')]
        # transform records into dict
        keys = {}
        for i in range(len(records)):
            keys[[x[:x.find('=')].strip() for x in records][i]] = [x[x.find('=') + 1:].strip() for x in records][i]
        cond = cmd[cmd.upper().find("WHERE") + 6:].strip() if cmd.upper().find("WHERE") > -1 else None
        # transform cond into a dict
        if not cond == None:
            cond = {cond[:cond.find('=')].strip(): re.sub(r'[\'"]', '', cond[cond.find('=') + 1:]).strip()}
        update(table, keys, cond)
    elif cmd[:11].upper() == "DELETE FROM":
        table = cmd[12:cmd.find(" ", 12)]
        # transform cond into a dict
        cond = cmd[cmd.upper().find("WHERE") + 6:].strip() if cmd.upper().find("WHERE") > -1 else None
        if not cond == None:
            cond = {cond[:cond.find('=')].strip(): re.sub(r'[\'"]', '', cond[cond.find('=') + 1:]).strip()}
        delete(table, cond)
    elif cmd[:11].upper() == "START TIMER":
        current_time = time.time()
        if PRINT_INFO:
            print("Started timer")
    elif cmd[:9].upper() == "GET TIMER":
        print(f"Timer at {time.time() - current_time} seconds")
    elif cmd[:5].upper() == "PRINT":
        print(cmd[6:])
    else:
        # raise SyntaxError(f"Command {cmd} could not be parsed")
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
        # raise FileExistsError(f"Database {full_path} already exists.")
        print(f"ERROR: Database {full_path} already exists.")

def drop_database(name, path = ".", check = False):
    """Delete databases.

    Arguments:
    name -- Name of the database to delete
    path -- Filepath to a directory where the database is (default is the current directory)
    check -- Check if the database exists first

    Raises:
    FileNotFoundError if the given name and path do not lead to a database.
    """
    full_path = os.path.abspath(os.path.join(os.path.expanduser(path), name))
    try:
        os.rmdir(full_path)
        if PRINT_INFO:
            print(f"Deleted database {name} at {os.path.join(path, name)}")
    except FileNotFoundError:
        if not check:
            # raise FileNotFoundError(f"Directory {full_path} does not exist.")
            print(f"ERROR: Directory {full_path} does not exist.")
    except OSError:
        print(f"WARNING: Database {name} is not empty. Drop anyways? (y/n):")
        res = input()
        if res[0] == 'y':
            shutil.rmtree(full_path)
            print(f"Deleted database {name} at {os.path.join(path, name)}")
            return
        else:
            return
        # raise OSError(f"Database {name} is not empty. Drop the tables first.")
        print(f"ERROR: Database {name} is not empty. Drop the tables first.")

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
        # raise FileNotFoundError(f"Directory {full_path} does not exist")
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
        # raise RuntimeError("No database in use")
        print("ERROR: No database in use")
    elif os.path.exists(path):
        # raise FileExistsError(f"Table {path} already exists")
        print(f"ERROR: Table {path} already exists")
    else:
        for col in columns:
            if not validate_datatype(col[1]):
                # raise SyntaxError(f"Column: {col} has illegal datatype")
                print(f"ERROR: Column: {col} has illegal datatype")
        with open(path, "w") as table:
            table.write("|".join([f"{col[0]} {col[1]}" for col in columns]))
        if PRINT_INFO:
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
        # raise RuntimeError("No database in use")
        print("ERROR: No database in use")
    else:
        try:
            os.remove(path)
            if PRINT_INFO:
                print(f"Dropped table {name}")
        except FileNotFoundError:
            # raise FileNotFoundError(f"Table {path} does not exist.")
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
        # raise RuntimeError("No database in use")
        print("ERROR: No database in use")
    else:
        try:
            with open(os.path.join(current_database, name), "r") as inFile:
                lines = inFile.readlines()
            if cmd[:3].upper() == "ADD":
                if PRINT_INFO:
                    print(f"Adding column {cmd[4:]} to table {name}")
                lines[0] = lines[0].replace("\n", "") + f"|{cmd[4:]}\n"
                for i in range(len(lines) - 1):
                    lines[i + 1] = lines[i + 1].replace("\n", "") + '|""\n'
            elif cmd[:11].upper() == "DROP COLUMN":
                column = cmd[12:]

                if PRINT_INFO:
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
                    # raise SyntaxError(f"Column {column} not in table {name}")
                    print(f"ERROR: Column {column} not in table {name}")
                    return
            with open(os.path.join(current_database, name), "w") as outFile:
                outFile.writelines(lines)
        except FileNotFoundError:
            print(f"ERROR: Table {name} does not exist.")

def create_index(name, table, column):
    """Create a B+ tree index on a column for faster queries.

    Arguments:
    name -- Name of the index.
    table -- Table to create the index on.
    column -- Column to create the index on.

    Raises:
    FileNotFoundError if the given name does not lead to a table.
    RuntimeError if there is no database being used, or if the column is
        not present in the table.
    """
    if current_database == "":
        # raise RuntimeError("No database in use")
        print("ERROR: No database in use")
    else:
        global PRINT_INFO
        path = os.path.join(current_database, table)
        if not os.path.exists(path):
            # raise FileNotFoundError(f"Table {table} does not exist")
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

        header = lines[0]
        head = [x[:x.find(" ")] for x in header]

        if column not in head:
            # raise RuntimeError(f"Column {column} not found in {table}")
            print(f"ERROR: Column {column} not found in {table}")
            return
        if table not in indexes:
            indexes[table] = {}
        # NOTE: Magic number degree is from assignment spec
        indexes[table][column] = BPlusTree(10)
        for line in lines[1:]:
            indexes[table][column].insert(line, line[head.index(column)])

        if PRINT_INFO:
            print(f"Created index {name} on {table}({column})")

def load_csv(name, table):
    """Load data from a CSV file into a table.

    Arguments:
    name -- Name of the CSV file to load, including extension. Must have
        the same number of columns as the table.
    table -- Table to load the data into.

    Raises:
    FileNotFoundError if the given name does not lead to a CSV file, or
        the given table does not lead to a table.
    RuntimeError if there is no database being used, or if the number of
        columns in the CSV file does not match the table.
    """
    if current_database == "":
        # raise RuntimeError("No database in use")
        print("ERROR: No database in use")
    else:
        global PRINT_INFO
        if not os.path.exists(name):
            # raise FileNotFoundError(f"CSV file {name} does not exist")
            print(f"ERROR: CSV file {name} does not exist")
            return
        path = os.path.join(current_database, table)
        if not os.path.exists(path):
            # raise FileNotFoundError(f"Table {table} does not exist")
            print(f"ERROR: Table {table} does not exist")
            return
        rows = []
        with open(name, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            for row in reader:
                rows.append(row)
        temp = PRINT_INFO
        PRINT_INFO = False
        insert(table, rows)
        PRINT_INFO = temp
        if PRINT_INFO:
            print(f"Loaded {len(rows)} records into {table} from {name}")

def select(columns, table, condition = None):
    """Select data from a table.

    Arguments:
    columns -- Which columns to select. Either list of string column names, or "*" for all columns.
    table -- Which table to select from.
    condition -- Conditions to select data on (default is None)

    Raises:
    FileNotFoundError if the given table does not lead to a table.
    RuntimeError if there is no database being used.

    Returns:
    List of lists, with the first entry represeting table columns and subsequent entries
    representing individual records.
    """
    if current_database == "":
        # raise RuntimeError("No database in use")
        print("ERROR: No database in use")
    else:
        global PRINT_INFO
        if ", " in table:
            # implicit inner join
            temp = PRINT_INFO
            PRINT_INFO = False
            selections = {}
            tables = table.split(", ")
            for i in range(len(tables)):
                if ' ' in tables[i]:
                    alias = tables[i].split(' ')
                    temp = {}
                    condition = {c.replace(alias[1], alias[0]): {"comp": condition[c]["comp"], "value": condition[c]["value"].replace(alias[1], alias[0])} for c in condition}
                    tables[i] = alias[0]
                selections[tables[i]] = select(columns, tables[i])
            PRINT_INFO = temp
            
            heads = {tbl: [head[:head.find(' ')] for head in selections[tbl][0]] for tbl in tables}
            joined = [selections[tables[0]][0]]
            joined[0] += [x for x in selections[tables[1]][0] if x not in joined[0]]

            matching = [[key[key.find('.') + 1:], condition[key]["value"][condition[key]["value"].find('.') + 1:]] for key in condition]
            data = []
            for a in selections[tables[0]][1:]:
                for b in selections[tables[1]][1:]:
                    if a[heads[tables[0]].index(matching[0][0])] == b[heads[tables[1]].index(matching[0][1])]:
                        aDict = {key: a[heads[tables[0]].index(key)] for key in heads[tables[0]]}
                        bDict = {key: b[heads[tables[1]].index(key)] for key in heads[tables[1]]}
                        data.append(join_records(aDict, bDict))

            joined += data
            if PRINT_INFO:
                print(f"Selecting {len(joined) - 1} records from tables {', '.join(tables)}")
            return joined
        elif "JOIN" in table.upper():
            # explicit join of some sort
            outerJoin = "LEFT OUTER JOIN" in table.upper()
            tables = [table[:table.find(' ')]]
            if outerJoin:
                tables += [table[table.find('LEFT OUTER JOIN') + 16:table.find(' ', table.find('LEFT OUTER JOIN') + 16)]]
            else:
                tables += [table[table.find('INNER JOIN') + 11:table.find(' ', table.find('INNER JOIN') + 11)]]

            temp = PRINT_INFO
            PRINT_INFO = False
            selections = {}
            for tbl in tables:
                selections[tbl] = select(columns, tbl)
            PRINT_INFO = temp

            heads = {tbl: [head[:head.find(' ')] for head in selections[tbl][0]] for tbl in tables}

            joined = [selections[tables[0]][0]]
            joined[0] += [x for x in selections[tables[1]][0] if x not in joined[0]]
            matching = [[key[key.find('.') + 1:], condition[key][condition[key].find('.') + 1:]] for key in condition]
            data = []
            for a in selections[tables[0]][1:]:
                flag = False
                for b in selections[tables[1]][1:]:
                    if a[heads[tables[0]].index(matching[0][0])] == b[heads[tables[1]].index(matching[0][1])]:
                        aDict = {key: a[heads[tables[0]].index(key)] for key in heads[tables[0]]}
                        bDict = {key: b[heads[tables[1]].index(key)] for key in heads[tables[1]]}
                        data.append(join_records(aDict, bDict))
                        flag = True
                if outerJoin and not flag:
                    data.append(a)

            joined += data
            if PRINT_INFO:
                print(f"Selecting {len(joined) - 1} records from tables {', '.join(tables)}")
            return joined
        else:
            path = os.path.join(current_database, table)
            if not os.path.exists(path):
                # raise FileNotFoundError(f"Table {table} does not exist")
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

            header = lines[0]
            head = [x[:x.find(" ")] for x in header]
            if condition and table in indexes and all([x in indexes[table] for x in condition]):
                col = [k for k in condition][0]
                if condition[col][0]['comp'] == '=':
                    selected = indexes[table][col].search(condition[col][0]['value'])
                elif len(condition[col]) == 2:
                    less = condition[col][0] if condition[col][0]['comp'] == '<' else condition[col][1]
                    more = condition[col][1] if less == condition[col][0] else condition[col][0]
                    selected = indexes[table][col].search_range(more['value'], less['value'])
                elif condition[col][0]['comp'] == '>':
                    selected = indexes[table][col].search_range(condition[col][0]['value'])
                elif condition[col][0]['comp'] == '<':
                    selected = indexes[table][col].search_range(None, condition[col][0]['value'])
                selected = [[record[i] for i in range(len(record)) if head[i] in columns or columns[0] == '*'] for record in selected]
            else:
                col = [k for k in condition][0] if condition else None
                selected = lines[1:]
                if col == None:
                    selected = [record for record in selected if condition == None or len([key for key in condition if record[head.index(key)] == str(condition[key][0]['value'])]) == len(condition)]
                elif condition[col][0]['comp'] == '=':
                    selected = [record for record in selected if condition == None or len([key for key in condition if record[head.index(key)] == str(condition[key][0]['value'])]) == len(condition)]
                elif len(condition[col]) == 2:
                    less = condition[col][0] if condition[col][0]['comp'] == '<' else condition[col][1]
                    more = condition[col][1] if less == condition[col][0] else condition[col][0]
                    selected = [record for record in selected if condition == None or len([key for key in condition if int(record[head.index(key)]) < int(less['value']) and int(record[head.index(key)]) > int(more['value'])]) == len(condition)]
                elif condition[col][0]['comp'] == '>':
                    selected = [record for record in selected if condition == None or len([key for key in condition if int(record[head.index(key)]) > int(condition[key][0]['value'])]) == len(condition)]
                elif condition[col][0]['comp'] == '<':
                    selected = [record for record in selected if condition == None or len([key for key in condition if int(record[head.index(key)]) < int(condition[key][0]['value'])]) == len(condition)]
                selected = [[record[i] for i in range(len(record)) if head[i] in columns or columns[0] == '*'] for record in selected]
            head = [h for h in head if h in columns or columns[0] == '*']
            header = [h for h in header if any([x in h for x in head])]
            joined = [header] + selected

            if PRINT_INFO:
                print(f"Selecting {len(selected)} records from table {table}")
            return joined

def insert(table, values, columns = None):
    """Insert records into a table.

    Arguments:
    table -- Which table to insert into
    values -- The records to insert. List of tuples
    columns -- Which columns to insert into (default is None)

    Raises:
    FileNotFoundError if the given table does not lead to a table.
    RuntimeError if there is no database being used, or if a column is not present in the table.
    SyntaxError if the lengths of values and columns do not match.
    """
    if current_database == "":
        # raise RuntimeError("No database in use")
        print("ERROR: No database in use")
    else:
        path = os.path.join(current_database, table)
        if not os.path.exists(path):
            # raise FileNotFoundError(f"Table {table} does not exist")
            print(f"ERROR: Table {table} does not exist")
            return
        if (not columns == None) and (not len(values[0]) == len(columns)):
            # raise SyntaxError(f"Length of values and columns does not match")
            print(f"ERROR: Length of values and columns does not match")
            return
        with open(path, "r") as reader:
            tableColumns = reader.readline().split("|")
        tableColumns = [x[:x.find(" ")] for x in tableColumns]
        if not columns == None:
            for col in columns:
                if not col in tableColumns:
                    # raise RuntimeError(f"Column {col} not found in {table}")
                    print(f"ERROR: Column {col} not found in {table}")
                    return
        if PRINT_INFO:
            print(f"Inserting {len(values)} records into {table}")
        out = []
        for value in values:
            out.append([value[tableColumns.index(x)] if columns == None or x in columns else "" for x in tableColumns])
        with open(path, 'a') as writer:
            writer.writelines([f'\n"{'"|"'.join(map(str, x))}"' for x in out])

def update(table, values, condition = None):
    """Update records in a table.

    Arguments:
    table -- Which table to update
    values -- The columns to update. Dictionary
    condition -- Conditions to select data on (default is None)

    Raises:
    FileNotFoundError if the given table does not lead to a table.
    RuntimeError if there is no database being used.
    """
    if current_database == "":
        # raise RuntimeError("No database in use")
        print("ERROR: No database in use")
    else:
        path = os.path.join(current_database, table)
        if not os.path.exists(path):
            # raise FileNotFoundError(f"Table {table} does not exist")
            print(f"ERROR: Table {table} does not exist")
            return
        global PRINT_INFO
        temp = PRINT_INFO
        PRINT_INFO = False

        selection = select(["*"], table, condition)
        PRINT_INFO = temp

        cols = selection.pop(0)
        head = [x[:x.find(" ")] for x in cols]
        recordCount = 0

        for record in selection:
            if condition == None:
                for value in values:
                    record[head.index(value)] = values[value]
                recordCount += 1
            else:
                for key in condition:
                    if record[head.index(key)] == str(condition[key]):
                        for value in values:
                            record[head.index(value)] = values[value]
                        recordCount += 1
                        break
        if PRINT_INFO:
            print(f"Updating {recordCount} records from {table}")
        with open(path, "w") as writer:
            writer.writelines(['|'.join(cols), *['\n"' + '"|"'.join(x) + '"' for x in selection]])

def delete(table, condition = None):
    """Delete records from a table.

    Arguments:
    table -- Which table to delete from
    condition -- Conditions to select data on. Dictionary format for column: value (default is None)

    Raises:
    FileNotFoundError if the given table does not lead to a table.
    RuntimeError if there is no database being used.
    """
    if current_database == "":
        # raise RuntimeError("No database in use")
        print("ERROR: No database in use")
    else:
        path = os.path.join(current_database, table)
        if not os.path.exists(path):
            # raise FileNotFoundError(f"Table {table} does not exist")
            print(f"ERROR: Table {table} does not exist")
            return
        global PRINT_INFO
        temp = PRINT_INFO
        PRINT_INFO = False
        selection = select(["*"], table)
        PRINT_INFO = temp

        cols = selection.pop(0)
        head = [x[:x.find(" ")] for x in cols]
        recordCount = len(selection)
        selection = [row for row in selection if not condition == None and not len([key for key in condition if row[head.index(key)] == str(condition[key])]) > 0]

        if PRINT_INFO:
            print(f"Deleting {recordCount - len(selection)} records from table {table}")
        with open(path, "w") as writer:
            writer.writelines(['|'.join(cols), *['\n"' + '"|"'.join(x) + '"' for x in selection]])

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

def join_records(a, b):
    """Join two record dicts together

    Arguments:
    a -- a dictionary containing keys (columns) and values (record values)
    b -- a dictionary containing keys (columns) and values (record values)

    Returns:
    array record with columns in order of a-first, then b
    """
    return [a[key] for key in a] + [b[key] for key in b if key not in a.keys()]

def print_table(rows):
    """Print a table (list of lists) in a pretty format"""
    if rows == None: return
    rows = [[row[i] if i < len(row) else '' for i in range(len(rows[0]))] for row in rows]
    widths = [max([len(str(row[i])) for row in rows]) for i in range(len(rows[0]))]
    for row in rows:
        for i in range(len(rows[0])):
            print(f"+{'-' * (widths[i] + 2)}", end = "")
        print("+")
        for j in range(len(rows[0])):
            print(f"|{row[j].center(widths[j] + 2)}", end = "")
        print("|")
    # Last line
    for k in range(len(rows[0])):
        print(f"+{'-' * (widths[k] + 2)}", end = "")
    print("+")

def test():
    """Testing"""
    return

if __name__ == "__main__":
    main()