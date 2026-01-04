# -*- coding: utf-8 -*-
import sys
import os
import json
import io
import uuid
import traceback
from pyrevit import script, DB, revit
from System.Collections.Generic import List

output = script.get_output()
output.print_md("# 🏗️ BEM FACTORY: Floor Fix Edition")

JSON_SOURCE = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\bem_update_package_FULL.json"


# --- 1. DATA LOADER ---
def get_data():
    if not os.path.exists(JSON_SOURCE): return None
    with io.open(JSON_SOURCE, 'r', encoding='utf-8') as f:
        data = json.loads(f.read())

    # PATCH DATA
    data["FOR CAM SANIT"] = [
        {"material_name": "Plaqueta o baldosa de gres",
         "properties_si": {"k": 2.3, "d": 2500, "cp": 1000, "thickness": 0.010}},
        {"material_name": "Mortero de cemento o cal (1000-1250)",
         "properties_si": {"k": 0.55, "d": 1125, "cp": 1000, "thickness": 0.025}},
        {"material_name": "Mortero de cemento de difusion",
         "properties_si": {"k": 0.55, "d": 1500, "cp": 800, "thickness": 0.060}},
        {"material_name": "Poliestireno Expandido XPS",
         "properties_si": {"k": 0.034, "d": 1500, "cp": 800, "thickness": 0.100}},
        {"material_name": "FU Entrevigado de EPS (Canto 300)",
         "properties_si": {"k": 0.256, "d": 750, "cp": 1000, "thickness": 0.300}},
        {"material_name": "Cloruro de polivinilo (PVC)",
         "properties_si": {"k": 0.17, "d": 1390, "cp": 900, "thickness": 0.005}}
    ]
    if "TAB INT" not in data and "Tabique Interior" in data: data["TAB INT"] = data["Tabique Interior"]
    if "FOR INT" not in data and "FOR INT AC-NH" in data: data["FOR INT"] = data["FOR INT AC-NH"]
    return data


# --- 2. HELPERS ---
def get_safe_name(element):
    if not element: return "None"
    param = element.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if param and param.HasValue: return param.AsString()
    try:
        return element.Name
    except:
        return "UNKNOWN"


# --- 3. MATERIAL HANDLER (UUID FIX) ---
def get_material(doc, item):
    name = item.get('material_name', 'Unknown')

    mat = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material) if m.Name == name), None)
    if not mat: mat = doc.GetElement(DB.Material.Create(doc, name))

    # Generate Unique Asset Name
    unique_id = str(uuid.uuid4())[:8]
    asset_name = "{}_Termico_{}".format(name, unique_id)

    if mat.ThermalAssetId != DB.ElementId.InvalidElementId:
        mat.ThermalAssetId = DB.ElementId.InvalidElementId

    si = item.get('properties_si', {})
    new_asset = DB.ThermalAsset(asset_name, DB.ThermalMaterialType.Solid)
    new_asset.ThermalConductivity = DB.UnitUtils.ConvertToInternalUnits(float(si.get('k', 0.1)),
                                                                        DB.UnitTypeId.WattsPerMeterKelvin)
    new_asset.Density = DB.UnitUtils.ConvertToInternalUnits(float(si.get('d', 1000)),
                                                            DB.UnitTypeId.KilogramsPerCubicMeter)
    new_asset.SpecificHeat = DB.UnitUtils.ConvertToInternalUnits(float(si.get('cp', 1000)),
                                                                 DB.UnitTypeId.JoulesPerKilogramDegreeCelsius)

    pse = DB.PropertySetElement.Create(doc, new_asset)
    mat.ThermalAssetId = pse.Id
    return mat.Id


# --- 4. BUILDER (ENDCAP FIX) ---
def get_or_create_type(doc, type_name):
    print("\n[Processing] '{}'".format(type_name))
    name_upper = type_name.upper()

    if any(x in name_upper for x in ["MURO", "TAB", "PARTICION", "FACHADA"]):
        target_class = DB.WallType
    elif any(x in name_upper for x in ["FOR", "SOL", "LOSA"]):
        target_class = DB.FloorType
    elif any(x in name_upper for x in ["CUB", "TEJA"]):
        target_class = DB.RoofType
    else:
        return None

    collector = DB.FilteredElementCollector(doc).OfClass(target_class)
    all_elements = list(collector)

    # Check Existing
    for e in all_elements:
        if get_safe_name(e).upper() == name_upper:
            print("   ✅ Found existing type.")
            return e

    # Duplicate Donor
    donor = next((e for e in all_elements if e.GetCompoundStructure()), None)
    if not donor:
        print("   ❌ CRITICAL: No donor found.")
        return None

    try:
        print("   ✨ Creating New Type (Donor: '{}')".format(get_safe_name(donor)))
        return donor.Duplicate(type_name)
    except:
        return None


def build_layers(doc, element_type, layers_list):
    try:
        # 1. Prepare Layers
        max_th = 0
        core_idx = 0
        for i, l in enumerate(layers_list):
            t = float(l['properties_si']['thickness'])
            if t > max_th: max_th = t; core_idx = i

        rvt_layers = []
        print("   🔨 Building {} layers...".format(len(layers_list)))

        for i, l_data in enumerate(layers_list):
            mat_id = get_material(doc, l_data)
            th_m = float(l_data['properties_si']['thickness'])
            th_rvt = DB.UnitUtils.ConvertToInternalUnits(th_m, DB.UnitTypeId.Meters)
            if th_rvt < 0.0015: th_rvt = 0.0015

            if i == core_idx:
                func = DB.MaterialFunctionAssignment.Structure
            elif i < core_idx:
                func = DB.MaterialFunctionAssignment.Finish1
            else:
                func = DB.MaterialFunctionAssignment.Finish2

            rvt_layers.append(DB.CompoundStructureLayer(th_rvt, func, mat_id))

        # 2. GET EXISTING STRUCTURE (The Fix)
        # Instead of creating new, we edit the existing one to preserve Category settings (EndCaps)
        cs = element_type.GetCompoundStructure()

        if not cs:
            # Fallback if somehow no structure exists
            cs = DB.CompoundStructure.CreateSimpleCompoundStructure(List[DB.CompoundStructureLayer](rvt_layers))
        else:
            # Overwrite the layers of the existing structure
            cs.SetLayers(List[DB.CompoundStructureLayer](rvt_layers))

        # 3. Set Core Boundaries
        cs.SetNumberOfShellLayers(DB.ShellLayerType.Exterior, core_idx)
        cs.SetNumberOfShellLayers(DB.ShellLayerType.Interior, (len(rvt_layers) - 1) - core_idx)

        # 4. Commit
        element_type.SetCompoundStructure(cs)
        return True
    except Exception as e:
        print("   ❌ Layer Build Failed: {}".format(e))
        traceback.print_exc()
        return False


# --- MAIN ---
def run():
    doc = __revit__.ActiveUIDocument.Document
    data = get_data()
    if not data: return

    t = DB.Transaction(doc, "BEM Final Build")
    t.Start()

    try:
        count = 0
        for name, layers in data.items():
            typ = get_or_create_type(doc, name)
            if typ:
                if build_layers(doc, typ, layers):
                    count += 1

        t.Commit()
        output.print_md("### ✅ Success! Processed {} Assemblies.".format(count))

    except Exception as e:
        t.RollBack()
        print("\n🔥 CRITICAL FAILURE 🔥")
        print(str(e))


if __name__ == "__main__":
    run()