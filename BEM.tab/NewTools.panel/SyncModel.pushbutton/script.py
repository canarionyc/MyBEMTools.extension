# -*- coding: utf-8 -*-
import sys
import os
import json
from pyrevit import script, DB, revit
from System.Collections.Generic import List

output = script.get_output()
output.print_md("# 🏗️ STEP 2: Model Sync (Final)")

# --- CONFIG ---
JSON_SOURCE = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\bem_update_package.json"


def clean_slate_asset(doc, asset_name, current_asset_id):
    """
    Surgical removal of the specific asset to prevent naming collisions.
    """
    ids_to_delete = []

    if current_asset_id != DB.ElementId.InvalidElementId:
        ids_to_delete.append(current_asset_id)

    collector = DB.FilteredElementCollector(doc).OfClass(DB.PropertySetElement)
    for e in collector:
        if e.Name == asset_name:
            ids_to_delete.append(e.Id)

    if ids_to_delete:
        unique_ids = list(set(ids_to_delete))
        revit_ids = List[DB.ElementId](unique_ids)
        try:
            print("    [DELETE] Removing {} old asset(s) named '{}'...".format(len(unique_ids), asset_name))
            doc.Delete(revit_ids)
            doc.Regenerate()
            print("    [REFRESH] Revit memory cache cleared.")
        except Exception as e:
            print("    [WARNING] Delete failed: {}".format(e))


def get_or_create_material_with_asset(doc, item):
    mat_name = item['material_name']
    asset_name = item['asset_name']
    props = item['properties']
    si_props = item.get('debug_si', {})  # Get original SI units if available for reference

    # --- A. MATERIAL HANDLING ---
    mat = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material) if m.Name == mat_name), None)
    if not mat:
        print("    [CREATE] New Material: '{}'".format(mat_name))
        mat = doc.GetElement(DB.Material.Create(doc, mat_name))
    else:
        print("    [FOUND] Existing Material: '{}'".format(mat_name))

    # --- B. THERMAL ASSET (DELETE & INSERT) ---
    if mat.ThermalAssetId != DB.ElementId.InvalidElementId:
        mat.ThermalAssetId = DB.ElementId.InvalidElementId

    clean_slate_asset(doc, asset_name, mat.ThermalAssetId)

    # --- C. PRE-FLIGHT LOGGING (Obsessive Logger) ---
    print("    [PREP] Preparing Asset: '{}'".format(asset_name))
    print(
        "      |-- Conductivity:  {:.5f} BTU/(h·ft·°F)  [SI: {} W/(m·K)]".format(props['k'], si_props.get('k', 'N/A')))
    print("      |-- Density:       {:.5f} lb/ft³         [SI: {} kg/m³]".format(props['d'], si_props.get('d', 'N/A')))
    print("      |-- Specific Heat: {:.5f} BTU/(lb·°F)    [SI: {} J/(kg·K)]".format(props['cp'],
                                                                                    si_props.get('cp', 'N/A')))

    # Create Object
    new_asset = DB.ThermalAsset(asset_name, DB.ThermalMaterialType.Solid)
    new_asset.ThermalConductivity = props['k']
    new_asset.Density = props['d']
    new_asset.SpecificHeat = props['cp']

    print("    [INSERT] Creating fresh asset...")

    # --- THE FIX: Create returns ELEMENT, we need ID ---
    pse = DB.PropertySetElement.Create(doc, new_asset)

    mat.ThermalAssetId = pse.Id
    print("    [LINK] Asset linked to Material (ID: {}).".format(pse.Id))

    return mat.Id


def run_sync():
    doc = __revit__.ActiveUIDocument.Document

    print(">>> Loading Data Package...")
    if not os.path.exists(JSON_SOURCE):
        print("    [ERROR] JSON file not found.")
        return

    with open(JSON_SOURCE, 'r') as f:
        data = json.load(f)

    if not data:
        print("    [WARNING] Data package is empty.")
        return

    # --- TRANSACTION ---
    t = DB.Transaction(doc, "BEM: Sync SOL CAM SANIT")
    t.Start()

    try:
        # Find Floor Type
        target_name = data[0]['assembly']
        print("\n[SEARCH] Looking for FloorType: '{}'".format(target_name))

        target_type = next((ft for ft in DB.FilteredElementCollector(doc).OfClass(DB.FloorType)
                            if ft.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == target_name), None)

        if not target_type:
            print("    [ERROR] FloorType not found.")
            t.RollBack()
            return

        print("    [FOUND] FloorType ID: {}".format(target_type.Id))

        # Update Structure
        struct = target_type.GetCompoundStructure()

        for i, item in enumerate(data):
            if i < struct.LayerCount:
                print("\n    --- Processing Layer {} ---".format(i))
                mat_id = get_or_create_material_with_asset(doc, item)

                print("    [UPDATE] Setting Thickness: {} ft".format(round(item['thickness_ft'], 4)))
                struct.SetMaterialId(i, mat_id)
                struct.SetLayerWidth(i, item['thickness_ft'])

        target_type.SetCompoundStructure(struct)

        t.Commit()
        output.print_md("### ✅ SUCCESS: Model Updated")

    except Exception as e:
        print("\n    [CRITICAL FAILURE] {}".format(e))
        if t.GetStatus() == DB.TransactionStatus.Started:
            t.RollBack()
            print("    [SAFETY] Transaction Rolled Back.")


if __name__ == "__main__":
    run_sync()