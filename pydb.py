#! /bin/python
"""Python-based database management system.

Author: Raiden H
Updated: 26-05-21

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

    CREATE DATABASE <name> [path="./"]
    DROP DATABASE <name> [path="./"]
    USE DATABASE <name> [path="./"]

    CREATE TABLE <name> <columns>
    DROP TABLE <name>
    ALTER TABLE <name> <operation> ...
                    ADD <columns>
                    DROP COLUMN <column>

    SELECT <columns> FROM <table> WHERE <condition>
                        <tables> WHERE <condition>
                        <table> INNER JOIN <table> ON <condition>
                        <table> LEFT OUTER JOIN <table> ON <condition>

    INSERT INTO <table> [columns] VALUES <values>
    UPDATE <table> SET <columns=values> [WHERE <condition>]
    DELETE FROM <table> [WHERE <condition>]
"""

import os
import re
import sys

PRINT_INFO = True
current_database = ""

class BPlusTree:
    """B+ tree implementation for efficient selections

    Arguments:
    degree -- degree (minimum # child nodes, 1/2 maximum) of the B+ tree
    """
    def __init__(self, degree):
        self.degree = degree
        self.root = self.Node(self.degree)
    
    def __str__(self):
        return f"BPlusTree (degree {self.degree}): \n{self.root}"
        
    def example(self):
        """Set the tree to an example structure for testing
        """
        self.degree = 2
        self.root = self.Node(self.degree, [80], [
            self.Node(self.degree, [20, 60], [
                self.Node(self.degree, [10, 15, 18], [10, 15, 18]),
                self.Node(self.degree, [20, 30, 40, 50], [20, 30, 40, 50]),
                self.Node(self.degree, [60, 65], [60, 65])
            ]),
            self.Node(self.degree, [100, 120, 140], [
                self.Node(self.degree, [80, 85, 90], [80, 85, 90])
            ])
        ])
        self.root.values[0].values[0].next = self.root.values[0].values[1]
        self.root.values[0].values[1].next = self.root.values[0].values[2]
        self.root.values[0].values[2].next = self.root.values[1].values[0]
        
    def _search(self, value):
        """Underlying search implementation. Always returns a node
        
        Arguments:
        value -- Value to search for
        
        Returns:
        node -- Node the value is located in, or would be located in, whether or not the value is in the node
        """
        leaf = self.root
        while not leaf.is_leaf():
            for i in range(len(leaf.keys) + 1):
                temp = leaf.values[i]
                if i == len(leaf.keys):
                    temp = leaf.values[i]
                    break
                if leaf.keys[i] > value:
                    break
                
            leaf = temp
        return leaf
    
    def search(self, value):
        """Search the tree for a value
        
        Arguments:
        value -- Value to search for
        
        Returns:
        (Node, index) -- If value is found in the tree
        None -- If value is not in the tree
        """
        temp = self._search(value)
        return (temp, temp.values.index(value)) if value in temp.values else None
    
    def search_range(self, start, end):
        """Search the tree for a range of values
        
        Arguments:
        start -- Start of range (exclusive)
        end -- End of range (exclusive)
        
        Returns:
        value[] -- List of values inside the range in ascending order
        """
        node = self._search(start)
        out = []
        while True:
            for val in node.values:
                if val < end:
                    if val > start:
                        out.append(val)
                else:
                    return out
            if node.next:
                node = node.next
            else:
                return out

    def insert(self, value):
        pass
    
    def delete(self, value):
        pass

    class Node:
        def __init__(self, degree, keys = [], values = []):
            self.degree = degree
            self.keys = keys
            self.values = values
            self.next = None
        
        def __str__(self):
            return f'  Node (leaf: {self.is_leaf()})  Keys: {self.keys}  Values: [{'\n' + '\n'.join([str(val) for val in self.values]) if isinstance(self.values[0], BPlusTree.Node) else ' '.join([str(val) for val in self.values])}]'
        
        def is_leaf(self):
            return len(self.values) == 0 or not isinstance(self.values[0], BPlusTree.Node)
        
        def insert(self, value, key):
            pass

def main():
    """Handle input and pass it off to helper functions."""
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
        if 'ON' in cmd.upper():
            cond = cmd[cmd.upper().find("ON") + 3:].strip()
        else:
            cond = cmd[cmd.upper().find("WHERE") + 6:].strip() if "WHERE" in cmd.upper() else None
        # transform cond into a dict
        if not cond == None:
            cond = {cond[:cond.find('=')].strip(): re.sub(r'[\'"]', '', cond[cond.find('=') + 1:]).strip()}
        print_table(select(cols, table, cond))
    elif cmd[:11].upper() == "INSERT INTO":
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
    elif cmd[:5].upper() == "PRINT":
        print(cmd[6:])
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
        # raise RuntimeError("ERROR: No database in use")
        print("ERROR: No database in use")
    else:
        try:
            os.remove(path)
            if PRINT_INFO:
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

    Returns:
    List of lists, with the first entry represeting table columns and subsequent entries
    representing individual records.
    """
    if current_database == "":
        # raise RuntimeError("ERROR: No database in use")
        print("ERROR: No database in use")
    else:
        global PRINT_INFO
        if ", " in table:
            # TODO: allow joins checking for equality on mismatched field names
            # implicit inner join
            temp = PRINT_INFO
            PRINT_INFO = False
            selections = {}
            tables = table.split(", ")
            for i in range(len(tables)):
                if ' ' in tables[i]:
                    alias = tables[i].split(' ')
                    temp = {}
                    for cond in condition:
                        temp[cond.replace(alias[1] + '.', alias[0] + '.')] = condition[cond].replace(alias[1] + '.', alias[0] + '.')
                    condition = temp

                    tables[i] = alias[0]
                selections[tables[i]] = select(columns, tables[i])
            PRINT_INFO = temp

            heads = {tbl: [head[:head.find(' ')] for head in selections[tbl][0]] for tbl in tables}
            joined = [selections[tables[0]][0]]
            joined[0] += [x for x in selections[tables[1]][0] if x not in joined[0]]

            matching = [[key[key.find('.') + 1:], condition[key][condition[key].find('.') + 1:]] for key in condition]
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

            header = lines[0]
            head = [x[:x.find(" ")] for x in header]
            selected = [[line[x] for x in range(len(line)) if header[x][:header[x].find(" ")] in columns or columns[0] == "*"] for line in lines[1:]]
            selected = [record for record in selected if condition == None or len([key for key in condition if record[head.index(key)] == str(condition[key])]) == len(condition)]
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
        # raise RuntimeError("ERROR: No database in use")
        print("ERROR: No database in use")
    else:
        path = os.path.join(current_database, table)
        if not os.path.exists(path):
            # raise FileNotFoundError(f"ERROR: Table {table} does not exist")
            print(f"ERROR: Table {table} does not exist")
            return
        if (not columns == None) and (not len(values[0]) == len(columns)):
            # raise SyntaxError(f"ERROR: Length of values and columns does not match")
            print(f"ERROR: Length of values and columns does not match")
            return
        with open(path, "r") as reader:
            tableColumns = reader.readline().split("|")
        tableColumns = [x[:x.find(" ")] for x in tableColumns]
        if not columns == None:
            for col in columns:
                if not col in tableColumns:
                    # raise RuntimeError(f"ERROR: Column {col} not found in {table}")
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
        # raise RuntimeError("ERROR: No database in use")
        print("ERROR: No database in use")
    else:
        path = os.path.join(current_database, table)
        if not os.path.exists(path):
            # raise FileNotFoundError(f"ERROR: Table {table} does not exist")
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
        # raise RuntimeError("ERROR: No database in use")
        print("ERROR: No database in use")
    else:
        path = os.path.join(current_database, table)
        if not os.path.exists(path):
            # raise FileNotFoundError(f"ERROR: Table {table} does not exist")
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
    temp = BPlusTree(10)
    temp.example()
    search = temp.search(10) or ('None', '')
    print(search[0], search[1])
    print(temp.search_range(8, 91))
    return

if __name__ == "__main__":
    main()