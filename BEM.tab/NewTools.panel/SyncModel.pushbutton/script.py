# -*- coding: utf-8 -*-
import sys
import os
import json
import io  # <--- THE FIX for reading files
# noinspection PyUnresolvedReferences
from pyrevit import script, DB, revit
from System.Collections.Generic import List

output = script.get_output()
output.print_md("# 🏗️ STEP 2: Model Sync (Final)")

JSON_SOURCE = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\bem_update_package.json"
UNIT_DUMP_FILE = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\revit_units_dump.txt"

from bem_utils import dump_all_units
dump_all_units()

# --- 2. SATELLITE SAFE CONVERSION ---
def to_internal(value, type_id):
    return DB.UnitUtils.ConvertToInternalUnits(value, type_id)

def clean_slate_asset(doc, asset_name, current_asset_id):
    ids_to_delete = []
    if current_asset_id != DB.ElementId.InvalidElementId:
        ids_to_delete.append(current_asset_id)
    collector = DB.FilteredElementCollector(doc).OfClass(DB.PropertySetElement)
    for e in collector:
        if e.Name == asset_name:
            ids_to_delete.append(e.Id)
    if ids_to_delete:
        revit_ids = List[DB.ElementId](list(set(ids_to_delete)))
        try:
            doc.Delete(revit_ids)
            doc.Regenerate()
        except Exception:
            pass


def get_or_create_material_with_asset(doc, item):
    mat_name = item['material_name']
    asset_name = item['asset_name']
    si = item['properties_si']

    # Search for material
    mat = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material) if m.Name == mat_name), None)
    if not mat:
        mat = doc.GetElement(DB.Material.Create(doc, mat_name))

    # --- SATELLITE SAFE CONVERSION ---
    k_val = to_internal(si['k'], DB.UnitTypeId.WattsPerMeterKelvin)
    d_val = to_internal(si['d'], DB.UnitTypeId.KilogramsPerCubicMeter)

    # Try Celsius first, fallback to Kelvin
    try:
        cp_val = to_internal(si['cp'], DB.UnitTypeId.JoulesPerKilogramDegreeCelsius)
    except AttributeError:
        cp_val = to_internal(si['cp'], DB.UnitTypeId.JoulesPerKilogramKelvin)

    # Logging
    print("    [ASSET] '{}'".format(asset_name))
    print("      |-- K   (SI: {:.3f}) -> Internal: {:.5f}".format(si['k'], k_val))
    print("      |-- Rho (SI: {:.0f}) -> Internal: {:.5f}".format(si['d'], d_val))
    print("      |-- Cp  (SI: {:.0f}) -> Internal: {:.5f}".format(si['cp'], cp_val))

    # --- CLEAN & CREATE ---
    if mat.ThermalAssetId != DB.ElementId.InvalidElementId:
        mat.ThermalAssetId = DB.ElementId.InvalidElementId
    clean_slate_asset(doc, asset_name, mat.ThermalAssetId)

    new_asset = DB.ThermalAsset(asset_name, DB.ThermalMaterialType.Solid)
    new_asset.ThermalConductivity = k_val
    new_asset.Density = d_val
    new_asset.SpecificHeat = cp_val

    pse = DB.PropertySetElement.Create(doc, new_asset)
    mat.ThermalAssetId = pse.Id

    return mat.Id


def run_sync():
    # noinspection PyUnresolvedReferences
    doc = __revit__.ActiveUIDocument.Document

    print("\n>>> Loading Pure SI Data...")
    if not os.path.exists(JSON_SOURCE): return

    # --- THE MOJIBAKE FIX ---
    # We use io.open with explicit encoding='utf-8'
    # We read the file content first, then pass to json.loads
    with io.open(JSON_SOURCE, 'r', encoding='utf-8') as f:
        file_content = f.read()
        data = json.loads(file_content)

    t = DB.Transaction(doc, "BEM: Sync Safe Units")
    t.Start()

    try:
        target_name = data[0]['assembly']
        print("\n[SEARCH] FloorType: '{}'".format(target_name))
        target_type = next((ft for ft in DB.FilteredElementCollector(doc).OfClass(DB.FloorType)
                            if ft.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == target_name), None)

        if not target_type:
            print("    [ERROR] Type not found.")
            t.RollBack()
            return

        struct = target_type.GetCompoundStructure()

        for i, item in enumerate(data):
            if i < struct.LayerCount:
                print("\n    --- Layer {} ---".format(i))
                mat_id = get_or_create_material_with_asset(doc, item)

                th_val = to_internal(item['properties_si']['thickness'], DB.UnitTypeId.Meters)

                print("    [THICKNESS] SI: {:.4f}m -> Internal: {:.4f}".format(item['properties_si']['thickness'],
                                                                               th_val))
                struct.SetMaterialId(i, mat_id)
                struct.SetLayerWidth(i, th_val)

        target_type.SetCompoundStructure(struct)
        t.Commit()
        output.print_md("### ✅ SUCCESS: Model Updated")

    except Exception as e:
        print("\n    [FAILURE] {}".format(e))
        if t.GetStatus() == DB.TransactionStatus.Started: t.RollBack()


if __name__ == "__main__":
    run_sync()