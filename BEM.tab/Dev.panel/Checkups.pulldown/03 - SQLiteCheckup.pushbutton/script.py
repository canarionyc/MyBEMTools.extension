#! python3
import sys
import os
from pyrevit import script

output = script.get_output()

print("## CPYTHON ENGINE AUDIT ##")
print("Python Version: {}".format(sys.version))
print("Executable Path: {}".format(sys.executable))

print("\n## SYSTEM PATH (sys.path) ##")
for path in sys.path:
    print("- {}".format(path))

print("\n## ENVIRONMENT VARIABLES ##")
# Checking specifically for the one you set
py_path = os.environ.get('PYTHONPATH', 'NOT SET')
print("PYTHONPATH Variable: {}".format(py_path))

print("\n## MODULE TEST: sqlite3 ##")
try:
    import sqlite3
    print("[SUCCESS] sqlite3 imported successfully.")
    print("Source File: {}".format(sqlite3.__file__))
except ImportError as e:
    print("[FAILURE] Could not import sqlite3.")
    print("Error: {}".format(e))
except Exception as e:
    print("[ERROR] An unexpected error occurred: {}".format(e))

print("\n" + "="*60)

#! python3
import sys
import sqlite3

print("--- CPython 3.12 Test ---")
print("Python Version: " + sys.version)
print("SQLite3 Library: " + sqlite3.__file__)
print("SQLite3 Version: " + sqlite3.sqlite_version)