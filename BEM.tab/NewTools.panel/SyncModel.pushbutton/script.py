# -*- coding: utf-8 -*-
import sys
import os
import json
import io
from pyrevit import script, DB, revit
from System.Collections.Generic import List

output = script.get_output()
output.print_md("# 🏗️ STEP 2: Model Sync (Class + Comments)")

JSON_SOURCE = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\bem_update_package.json"


# --- HELPER: Class & Comments ---
def update_identity_data(doc, material, class_name):
    """
    Updates Identity Tab data: Class and Comments.
    """
    # 1. Update Class (Identity Tab)
    if class_name:
        try:
            old_class = material.MaterialClass
            material.MaterialClass = class_name
            print("      |-- [IDENTITY] Class: '{}' -> '{}'".format(old_class, class_name))
        except Exception as e:
            print("      |-- [WARN] Failed to set Class: {}".format(e))

    # 2. Update Comments to "CTE" (for easy searching)
    try:
        # Parameter: Comments (BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        p_comments = material.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if p_comments and not p_comments.IsReadOnly:
            p_comments.Set("CTE")
            print("      |-- [IDENTITY] Comments set to 'CTE'")
    except Exception as e:
        print("      |-- [WARN] Failed to set Comments: {}".format(e))


# --- STANDARD HELPERS ---
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
    mat_class = item.get('material_class', 'Generic')
    asset_name = item['asset_name']
    si = item['properties_si']

    # 1. Get/Create Material
    mat = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material) if m.Name == mat_name), None)
    if not mat:
        mat = doc.GetElement(DB.Material.Create(doc, mat_name))

    print("    [MATERIAL] '{}'".format(mat_name))

    # 2. UPDATE IDENTITY (Class + Comments)
    update_identity_data(doc, mat, mat_class)

    # 3. UNIT CONVERSION
    k_val = to_internal(si['k'], DB.UnitTypeId.WattsPerMeterKelvin)
    d_val = to_internal(si['d'], DB.UnitTypeId.KilogramsPerCubicMeter)

    try:
        cp_val = to_internal(si['cp'], DB.UnitTypeId.JoulesPerKilogramDegreeCelsius)
    except AttributeError:
        cp_val = to_internal(si['cp'], DB.UnitTypeId.JoulesPerKilogramKelvin)

    # 4. LOGGING
    print("      |-- [THERMAL] K: {:.3f} | Rho: {:.0f} | Cp: {:.0f}".format(si['k'], si['d'], si['cp']))

    # 5. ASSET RECREATION
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
    doc = __revit__.ActiveUIDocument.Document

    print("\n>>> Loading Data...")
    if not os.path.exists(JSON_SOURCE): return

    with io.open(JSON_SOURCE, 'r', encoding='utf-8') as f:
        data = json.loads(f.read())

    t = DB.Transaction(doc, "BEM: Sync Class & Comments")
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

                struct.SetMaterialId(i, mat_id)
                struct.SetLayerWidth(i, th_val)

        target_type.SetCompoundStructure(struct)
        t.Commit()
        output.print_md("### ✅ SUCCESS: Class & Comments Updated")

    except Exception as e:
        print("\n    [FAILURE] {}".format(e))
        if t.GetStatus() == DB.TransactionStatus.Started: t.RollBack()


if __name__ == "__main__":
    run_sync()