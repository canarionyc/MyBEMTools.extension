#! python3
import sys
import os
import sqlite3
from pyrevit import revit, DB, script

# --- 1. ENVIRONMENT STABILITY ---
if not hasattr(sys.stdout, 'flush'):
    sys.stdout.flush = lambda: None

# Path injection for local Python 3.12 (if not already handled by a bootstrap)
LOCAL_SITE = r'C:\Python312\Lib\site-packages'
if LOCAL_SITE not in sys.path:
    sys.path.insert(0, LOCAL_SITE)

from bem_env import sanitize_revit_name, update_material_thermal_data

# --- 2. THERMAL ASSET UPDATER ---
# def update_material_thermal_data(doc, data):
#     raw_name = data['material']
#     # --- PASO CRITICO: Limpiar el nombre antes de cualquier operación en Revit ---
#     revit_name = sanitize_revit_name(raw_name)
#
#     # Buscar el material con el nombre ya limpio
#     material = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material)
#                      if m.Name == revit_name), None)
#
#     if not material:
#         # Ahora .Create no fallará porque revit_name no tiene caracteres prohibidos
#         mat_id = DB.Material.Create(doc, revit_name)
#         material = doc.GetElement(mat_id)
#
#     # ... resto de la lógica de ThermalAsset ...
#
#     # Manage Thermal Asset
#     asset_id = material.ThermalAssetId
#     if asset_id == DB.ElementId.InvalidElementId:
#         # Create new asset if missing (strip <> for safety in name)
#         # safe_name = mat_name.replace("<", "").replace(">", "") + "_Thermal"
#         thermal_asset = DB.ThermalAsset(revit_name, DB.ThermalMaterialType.Solid)
#         pse = DB.PropertySetElement.Create(doc, thermal_asset)
#         material.ThermalAssetId = pse.Id
#     else:
#         pse = doc.GetElement(asset_id)
#
#     # Edit Asset Properties
#     # Note: PropertySetElement requires a structured update via SetThermalAsset
#     asset = pse.GetThermalAsset()
#     asset.ThermalConductivity = data['conductivity']
#     asset.Density = data['density']
#     asset.SpecificHeat = data['specificheat']
#     # You can also set asset.VapourDiffusivity if needed
#
#     pse.SetThermalAsset(asset)
#     return material.Id


# --- 3. MAIN EXECUTION ---
doc = revit.doc
output = script.get_output()
from bem_env import db_path

# Query to fetch the specific assembly sequence
query = """
select wc.name
     , wc.material
     , m.material_group
     , round(wc.thickness,3) as thickness
     , round(m.conductivity,3) as conductivity
     , round(m.resistance,3) as resistance
     , round(m.density,3) as density
     , round(m.specificheat,3) as specificheat
     , round(m.vapourdiffusivity,3) as vapourdiffusivity
from wallcons_long wc, materials m  where wc.name='SOL CAM SANIT' and wc.material=m.name
        order by wc.rowid; -- Assuming row order matches layer order \
"""

try:
    # A. Fetch Data from SQLite
    if not os.path.exists(db_path):
        raise Exception("Database not found at {}".format(db_path))
    # Force the connection to handle strings as UTF-8
    conn = sqlite3.connect(db_path)
    conn.text_factory = str  # In Python 3, 'str' is natively Unicode (UTF-8)
    conn.row_factory = sqlite3.Row

    # DEBUG: Check if the material exists in the database before joining
    test_query = "SELECT name FROM materials WHERE name LIKE 'Hormig%'"
    results = conn.execute(test_query).fetchall()
    for r in results:
        print("Found in DB: {}".format(r['name']))

        # Now run your main query
    db_layers = conn.execute(query).fetchall()
    conn.close()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Allows access by column name
    db_layers = conn.execute(query).fetchall()
    conn.close()

    if not db_layers:
        print("No data found for 'SOL CAM SANIT' in database.")
        sys.exit()

    # B. Apply to Revit
    # ... (imports and data fetching remain the same) ...

    # B. Apply to Revit using Manual Transaction
    t = DB.Transaction(doc, "BEM: Update Thermal Assets [SOL CAM SANIT]")
    t.Start()
    try:
        # Find Floor/Foundation Type
        target_name = "SOL CAM SANIT"
        target_type = next((ft for ft in DB.FilteredElementCollector(doc).OfClass(DB.FloorType)
                            if ft.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == target_name), None)

        if target_type:
            struct = target_type.GetCompoundStructure()

            for i, row in enumerate(db_layers):
                mat_id = update_material_thermal_data(doc, row)
                thickness_ft = row['thickness'] / 0.3048

                if i < struct.LayerCount:
                    struct.SetMaterialId(i, mat_id)
                    struct.SetLayerWidth(i, thickness_ft)
                    print(
                        "Layer {}: {} (k={}, t={}m)".format(i, row['material'], row['conductivity'], row['thickness']))

            target_type.SetCompoundStructure(struct)
            t.Commit()  # COMMIT HERE
            output.print_md("### SUCCESS: SOL CAM SANIT Updated")
        else:
            print("ERROR: Floor/Foundation Type 'SOL CAM SANIT' not found.")
            t.RollBack()

    except Exception as e:
        print("Process failed: {}".format(e))
        if t.GetStatus() == DB.TransactionStatus.Started:
            t.RollBack()  # ROLLBACK ON ERROR

except Exception as e:
    print("Process failed: {}".format(e))