# -*- coding: utf-8 -*-
import sys
import os
import json
from pyrevit import script, DB, revit

output = script.get_output()
output.print_md("# 🏗️ STEP 2: Model Sync (IronPython)")

# --- CONFIG ---
# Must match the output from Step 1
JSON_SOURCE = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\bem_update_package.json"


def get_or_create_material_with_asset(doc, item):
    """
    Handles Material Creation + Thermal Asset Management
    using the 'Override/Reset' strategy to fix internal errors.
    """
    mat_name = item['material_name']
    asset_name = item['asset_name']
    props = item['properties']

    # 1. Get/Create Material
    mat = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material) if m.Name == mat_name), None)
    if not mat:
        mat = doc.GetElement(DB.Material.Create(doc, mat_name))

    # 2. Create Fresh Asset Object (In Memory)
    # We do NOT use UnitUtils here. We use the pre-calculated floats from JSON.
    new_asset = DB.ThermalAsset(asset_name, DB.ThermalMaterialType.Solid)
    new_asset.ThermalConductivity = props['k']
    new_asset.Density = props['d']
    new_asset.SpecificHeat = props['cp']

    # 3. Inject Asset (Orphan-Safe)
    current_asset_id = mat.ThermalAssetId

    if current_asset_id == DB.ElementId.InvalidElementId:
        # Check for Orphan
        collector = DB.FilteredElementCollector(doc).OfClass(DB.PropertySetElement)
        orphan = next((e for e in collector if e.Name == asset_name), None)

        if orphan:
            print("    [FIX] Found orphan asset '{}'. Overwriting...".format(asset_name))
            orphan.SetThermalAsset(new_asset)
            mat.ThermalAssetId = orphan.Id
        else:
            print("    [NEW] Creating asset '{}'...".format(asset_name))
            pse_id = DB.PropertySetElement.Create(doc, new_asset)
            mat.ThermalAssetId = pse_id
    else:
        # Overwrite Existing
        pse = doc.GetElement(current_asset_id)
        # Rename if necessary (and possible)
        if pse.Name != asset_name:
            try:
                pse.Name = asset_name
            except:
                pass

        print("    [UPDATE] Refreshing asset '{}'...".format(asset_name))
        pse.SetThermalAsset(new_asset)

    return mat.Id


def run_sync():
    doc = __revit__.ActiveUIDocument.Document

    print(">>> Loading Data Package...")
    if not os.path.exists(JSON_SOURCE):
        print("    [ERROR] JSON file not found. Run Step 1 first.")
        return

    with open(JSON_SOURCE, 'r') as f:
        data = json.load(f)

    if not data:
        print("    [WARNING] Data package is empty.")
        return

    print("    [INFO] Loaded {} layers to process.".format(len(data)))

    # --- TRANSACTION ---
    t = DB.Transaction(doc, "BEM: Sync SOL CAM SANIT")
    t.Start()

    try:
        # Find Floor Type
        target_name = data[0]['assembly']  # Assuming all rows are for same assembly
        target_type = next((ft for ft in DB.FilteredElementCollector(doc).OfClass(DB.FloorType)
                            if ft.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == target_name), None)

        if not target_type:
            print("    [ERROR] FloorType '{}' not found.".format(target_name))
            t.RollBack()
            return

        # Update Structure
        struct = target_type.GetCompoundStructure()

        for i, item in enumerate(data):
            if i < struct.LayerCount:
                print("\n    --- Layer {} ({}) ---".format(i, item['material_name']))

                # Material & Asset
                mat_id = get_or_create_material_with_asset(doc, item)

                # Thickness
                struct.SetMaterialId(i, mat_id)
                struct.SetLayerWidth(i, item['thickness_ft'])

        target_type.SetCompoundStructure(struct)

        t.Commit()
        output.print_md("### ✅ SUCCESS: Model Updated")

    except Exception as e:
        print("    [CRITICAL FAILURE] {}".format(e))
        t.RollBack()


if __name__ == "__main__":
    run_sync()