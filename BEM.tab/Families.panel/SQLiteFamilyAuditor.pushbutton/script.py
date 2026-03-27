#! python3
from pprint import pprint
import sqlite3
from pyrevit import revit, DB, script
from bem_env import db_path
doc = revit.doc
output = script.get_output()

# --- CONFIGURATION ---
# Update this path to where you saved the uploaded hulc_data.sqlite
CONSTRUCTION_NAME = "SOL CAM SANIT"
TARGET_ID_INT = 1659623
FT_TO_MM = 304.8

def get_db_layers(construction_name):
    """Fetch layers from SQLite wallcons_long table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Query wallcons_long joined with materials to get thermal data
    query = """
    SELECT layer_order, material, thickness 
    FROM wallcons_long 
    WHERE name = ? 
    ORDER BY layer_order ASC
    """
    cursor.execute(query, (construction_name,))
    rows = cursor.fetchall()
    conn.close()
    print(rows)
    return rows

print("--- OBSESSIVE BEM CROSS-CHECK: SQLITE vs. REVIT ---")

# 1. Fetch DB Data
db_layers = get_db_layers(CONSTRUCTION_NAME)
if not db_layers:
    print("CRITICAL: Construction '{}' not found in SQLite database.".format(CONSTRUCTION_NAME))
else:
    print("Found {} layers in SQLite for '{}'".format(len(db_layers), CONSTRUCTION_NAME))
    for layer in db_layers:
        pprint(layer)

# 2. Get Revit Element
el = doc.GetElement(DB.Id(TARGET_ID_INT))
el_type = doc.GetElement(el.GetTypeId())
comp_struct = el_type.GetCompoundStructure()
revit_layers = comp_struct.GetLayers()

print("\n" + "="*80)
print("{:<10} | {:<25} | {:<25}".format("LAYER", "SQLITE (Ground Truth)", "REVIT MODEL"))
print("-" * 80)

# 3. Step-by-Step Comparison
for i in range(max(len(db_layers), len(revit_layers))):
    layer_num = i + 1
    
    # DB Info
    if i < len(db_layers):
        db_mat = db_layers[i][1]
        db_thick = db_layers[i][2] * 1000 # Convert m to mm
        db_str = "{} ({:.1f}mm)".format(db_mat[:20], db_thick)
    else:
        db_str = "---"

    # Revit Info
    if i < len(revit_layers):
        rv_layer = revit_layers[i]
        rv_thick = rv_layer.Width * FT_TO_MM
        mat_id = rv_layer.MaterialId
        if mat_id != DB.ElementId.InvalidElementId:
            rv_mat = doc.GetElement(mat_id).Name
        else:
            rv_mat = "<NO MATERIAL>"
        rv_str = "{} ({:.1f}mm)".format(rv_mat[:20], rv_thick)
    else:
        rv_str = "---"

    # Print Comparison Row
    print("{:<10} | {:<25} | {:<25}".format(layer_num, db_str, rv_str))

print("="*80)

# 4. Search for matching "CTE" materials in Revit
print("\n[MAPPING STATUS]")
all_revit_materials = DB.FilteredElementCollector(doc).OfClass(DB.Material).ToElements()
cte_materials = [m for m in all_revit_materials if "CTE" in (m.Comments or "")]

print("Revit Project contains {} materials with comment 'CTE'.".format(len(cte_materials)))

for db_order, db_mat_name, db_thick in db_layers:
    match = [m for m in cte_materials if m.Name.lower() == db_mat_name.lower()]
    if match:
        print("  [OK] Found match for '{}': {}".format(db_mat_name, output.linkify(match[0].Id)))
    else:
        print("  [!!] MISSING: Material '{}' is in DB but not in Revit (with CTE comment).".format(db_mat_name))