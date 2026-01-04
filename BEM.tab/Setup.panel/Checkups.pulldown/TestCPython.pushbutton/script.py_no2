#! python3
import sys
import os


# --- 1. THE ENVIRONMENT FIX ---
LOCAL_SITE = r'C:\Python312\Lib\site-packages'
LOCAL_LIB  = r'C:\Python312\Lib'

if LOCAL_SITE not in sys.path:
    inserted = False
    for i, path in enumerate(sys.path):
        if "pyRevit-Master" in path:
            sys.path.insert(i, LOCAL_SITE)
            sys.path.insert(i, LOCAL_LIB)
            inserted = True
            break
    if not inserted:
        sys.path.insert(1, LOCAL_SITE)

# --- 2. THE IO FIX (Monkey Patch) ---
# This fixes the "'ScriptIO' object has no attribute 'flush'" error
if not hasattr(sys.stdout, 'flush'):
    sys.stdout.flush = lambda: None

# --- 3. ROBUST IMPORTS ---
try:
    import pandas as pd
    import numpy as np
    from pyrevit import revit, DB, script
    output = script.get_output()
    print("--- BEM ENGINE: LOADED SUCCESSFULLY ---")
except Exception as e:
    print("CRITICAL IMPORT ERROR: {}".format(e))
    sys.exit()

# --- 4. SQLITE TEST ---
output.print_md("## Testing SQLite Connection")
import sqlite3
try:
    # Assuming hulc_data.sqlite is in the same folder as this script
    db_path = r'C:/ProyectosCTEyCEE/CTEHE2019/Proyectos/EjemploI_2526_Option1_Config1/output/hulc_data.sqlite'
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query the materials table (based on your previous file upload)
        cursor.execute("SELECT name, material_group FROM materials LIMIT 5")
        rows = cursor.fetchall()
        
        print("Successfully connected to: {}".format(os.path.basename(db_path)))
        print("Sample Materials from Database:")
        for row in rows:
            print("- {} ({})".format(row[0], row[1]))
            
        conn.close()
    else:
        print("SQLite Alert: 'hulc_data.sqlite' not found at {}".format(db_path))
except Exception as e:
    print("SQLite Error: {}".format(e))

# --- 5. PANDAS & NUMPY TEST ---
output.print_md("## Testing Pandas & Numpy")
df = pd.DataFrame({'Engine': ['CPython'], 'Version': [sys.version]})
print(df)
print("\nNumpy Random Array:")
print(np.random.rand(2,2))

print("\n--- TEST COMPLETE ---")