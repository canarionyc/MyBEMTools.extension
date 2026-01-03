#! python3
import sys
import os


# 1. THE FIX: Define your modern Python 3.12 paths
LOCAL_SITE = r'C:\Python312\Lib\site-packages'
LOCAL_LIB  = r'C:\Python312\Lib'

# 2. SURGICAL INSERTION
# We want to be BEFORE the pyRevit-Master site-packages, 
# but AFTER the core Python internal ZIP files.
if LOCAL_SITE not in sys.path:
    # We find the first instance of pyrevit in the path and jump in front of it
    inserted = False
    for i, path in enumerate(sys.path):
        if "pyRevit-Master" in path:
            sys.path.insert(i, LOCAL_SITE)
            sys.path.insert(i, LOCAL_LIB)
            inserted = True
            break
    
    # Fallback if no pyrevit path was found
    if not inserted:
        sys.path.insert(1, LOCAL_SITE)

# 3. ROBUST IMPORTS
try:
    import math
    import pandas as pd
    import numpy as np
    from pyrevit import revit, DB, script
    print("--- BEM ENGINE: SUCCESSFUL LOAD ---")
except Exception as e:
    print("--- CRITICAL IMPORT ERROR ---")
    print(str(e))
    # This helps us see if 'pytz' is still the one causing the crash
    import traceback
    traceback.print_exc()
    sys.exit()



# ... (rest of your wall audit code)

# --- Debugging Information ---
print("## Python sys.path:")
from pprint import pprint
pprint(sys.path)


import pytz
print("pytz location: " + pytz.__file__)


# 3. Now imports should work
import pandas as pd
import numpy as np
from pyrevit import revit, script

output = script.get_output()
output.print_md("# BEM Engine: Pandas & Numpy Active")
print("Pandas Version: {}".format(pd.__version__))



# --- Answering your questions ---
#
# Q: Do case matter in the import?
# A: Yes, Python imports are case-sensitive. `from PyRevit import Revit` is
#    different from `from pyrevit import revit`.
#
# Q: Should I write from PyRevit import Revit?
# A: The standard way to import the Revit API wrapper in pyRevit is:
#    `from pyrevit import revit` (all lowercase).
#    The `pyrevit` library is provided by the pyRevit runtime environment.
#
#    The `PyRevit` (PascalCase) stubs you have are for type hinting and
#    autocompletion in your IDE. They define the .NET side of the pyRevit API,
#    which is different from the Python scripting API (`pyrevit.*`).
#    The correct import for accessing the Revit document and selection is
#    the one you are already using.

import numpy as np
import pandas as pd

print("\n## numpy array:")
print(repr(np.arange(15).reshape(3, 5)))

df_dict = {'key 1': 1, 'key 2': 2, 'key 3': 3}
df = pd.DataFrame([df_dict])

print("\n## pandas DataFrame:")
print_html(df.to_html().replace('\n', ''))

from pyrevit import revit
for element in revit.get_selection():
    print(element)

# --- Your original logic starts here ---
# doc = revit.doc
# output = script.get_output()

# --- 4. SQLITE TEST ---
output.print_md("## Testing SQLite Connection")
import sqlite3
try:
    # Assuming hulc_data.sqlite is in the same folder as this script
    db_path = r"C:/ProyectosCTEyCEE/CTEHE2019/Proyectos/EjemploI_2526_Option1_Config1/output/hulc_data.sqlite"
    
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