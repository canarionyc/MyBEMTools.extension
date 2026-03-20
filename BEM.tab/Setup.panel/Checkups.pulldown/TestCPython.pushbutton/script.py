#! python3
import sys
import os

# --- 1. ENVIRONMENT SNAPSHOT ---
# We remember what the path looked like BEFORE we touched it
original_path = list(sys.path)
injected_paths = []

def inject_path(path_str):
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
        injected_paths.append(path_str)

# --- 2. APPLY FIXES ---
inject_path(r'C:\Python312\Lib\site-packages')
inject_path(r'C:\Python312\Lib')

# Fix the persistent IO 'flush' error if it hasn't been fixed yet
if not hasattr(sys.stdout, 'flush'):
    sys.stdout.flush = lambda: None

# --- 3. THE ACTUAL SCRIPT ---
try:
    import pandas as pd
    import numpy as np
    from pyrevit import revit, script
    
    output = script.get_output()
    print("--- BEM ENGINE: RUNNING ---")
    
    # ... YOUR MAIN LOGIC HERE ...
    print("Success: Processed model data.")

except Exception as e:
    import traceback
    print("Error during execution: {}".format(e))
    traceback.print_exc()

finally:
    # --- 4. THE CLEANUP (The "Reset" Button) ---
    # This ensures the SECOND run starts with a clean slate
    print("--- CLEANING ENVIRONMENT ---")
    for path in injected_paths:
        if path in sys.path:
            sys.path.remove(path)
    
    # Optional: Clear the module cache for 'problem' libraries 
    # to force them to re-validate on the next click
    for mod in ['pytz', 'pandas', 'numpy']:
        if mod in sys.modules:
            del sys.modules[mod]

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
print("Done")