#! python3
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
from pyrevit import revit, DB, script

# importlib.reload(bem_env)

import bem_env
# --- 1. ENVIRONMENT & OUTPUT SETUP ---
output = script.get_output()
output.print_md("# BEM SYNC: Obsessive Progress Log")

print(">>> STEP 1: Initializing Environment...")
LOCAL_SITE = r'C:\Python312\Lib\site-packages'
if LOCAL_SITE not in sys.path:
    print("    [DEBUG] Injecting site-packages: {}".format(LOCAL_SITE))
    sys.path.insert(0, LOCAL_SITE)

try:
    from bem_env import sanitize_revit_name, update_material_thermal_data, db_path

    print("    [SUCCESS] bem_env utilities loaded.")
except Exception as e:
    print("    [CRITICAL] Failed to load bem_env: {}".format(e))
    sys.exit()

# --- 2. DATABASE PHASE ---
print("\n>>> STEP 2: Connecting to BEM Database...")
print("    [INFO] Target Path: {}".format(db_path))

query = """
        SELECT wc.name, \
               wc.material, \
               m.material_group,
               round(wc.thickness, 3)   as thickness,
               round(m.conductivity, 3) as conductivity,
               round(m.density, 3)      as density,
               round(m.specificheat, 3) as specificheat
        FROM wallcons_long wc, \
             materials m
        WHERE wc.name = 'SOL CAM SANIT' \
          AND wc.material = m.name
        ORDER BY wc.rowid; \
        """

try:
    if not os.path.exists(db_path):
        raise Exception("File not found at specified path.")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    print("    [SUCCESS] Database connection established.")

    print("    [SQL] Executing assembly fetch for 'SOL CAM SANIT'...")
    db_layers = conn.execute(query).fetchall()
    conn.close()

    layer_count = len(db_layers)
    print("    [DATA] Found {} layers in database for this assembly.".format(layer_count))
    for i, row in enumerate(db_layers):
        print("           Layer {}: {} (t={}m, k={})".format(i, row['material'], row['thickness'], row['conductivity']))

    if layer_count == 0:
        print("    [WARNING] No data returned. Check if 'SOL CAM SANIT' exists in 'wallcons_long' table.")
        sys.exit()

except Exception as e:
    print("    [ERROR] Database Phase Failed: {}".format(e))
    sys.exit()

# --- 3. REVIT PHASE ---
print("\n>>> STEP 3: Initializing Revit Transaction...")
doc = revit.doc

t = DB.Transaction(doc, "BEM: Sync SOL CAM SANIT")
print("    [INFO] Transaction 'BEM: Sync SOL CAM SANIT' created.")

try:
    t.Start()
    print("    [STATUS] Transaction Started.")

    # A. Target Finding
    target_name = "SOL CAM SANIT"
    print("    [SEARCH] Looking for FloorType named '{}'...".format(target_name))

    target_type = next((ft for ft in DB.FilteredElementCollector(doc).OfClass(DB.FloorType)
                        if ft.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == target_name), None)

    if not target_type:
        print("    [FAILURE] FloorType '{}' not found in this Revit project.".format(target_name))
        t.RollBack()
        sys.exit()

    print("    [SUCCESS] Found FloorType ID: {}".format(target_type.Id))

    # B. Structure Processing
    struct = target_type.GetCompoundStructure()
    revit_layer_count = struct.LayerCount
    print("    [STRUCT] Revit Type has {} layers. Data has {} layers.".format(revit_layer_count, layer_count))

    for i, row in enumerate(db_layers):
        print("\n    --- Processing Layer {} ---".format(i))

        if i >= revit_layer_count:
            print("    [SKIP] Layer index {} exceeds Revit Type structure. Skipping.".format(i))
            continue

        print("    [BEM_ENV] Calling update_material_thermal_data for: {}".format(row['material']))
        # update_material_thermal_data already has its own prints in your bem_env.py
        mat_id = update_material_thermal_data(doc, row)

        thickness_ft = row['thickness'] / 0.3048
        print("    [REVIT] Applying MaterialID {} and Thickness {}ft".format(mat_id, round(thickness_ft, 4)))

        struct.SetMaterialId(i, mat_id)
        struct.SetLayerWidth(i, thickness_ft)

    # C. Finalizing
    print("\n    [FINISH] Re-applying CompoundStructure to FloorType...")
    target_type.SetCompoundStructure(struct)

    t.Commit()
    print("    [SUCCESS] Transaction Committed.")
    output.print_md("### SYNC COMPLETE: SOL CAM SANIT Updated Successfully")

except Exception as e:
    print("\n    [CRITICAL ERROR] Revit Phase Failed: {}".format(e))
    if t.GetStatus() == DB.TransactionStatus.Started:
        t.RollBack()
        print("    [STATUS] Transaction Rolled Back to protect model integrity.")

print("\n>>> SCRIPT EXECUTION FINISHED.")