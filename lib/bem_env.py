# -*- coding: utf-8 -*-
import sys
import os
import unicodedata
# noinspection PyUnresolvedReferences
from Autodesk.Revit import DB

# --- ENVIRONMENT SETUP ---
if not hasattr(sys.stdout, 'flush'):
    sys.stdout.flush = lambda: None

# --- CONSTANTS ---
db_path = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\hulc_data.sqlite"


# --- HELPER FUNCTIONS ---
def sanitize_revit_name(text):
    if not text:
        return "Unnamed_Material"

    nfkd_form = unicodedata.normalize('NFKD', str(text))
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    translations = {
        "<": "inf", ">": "sup", "[": "(", "]": ")",
        "{": "(", "}": ")", "|": "-", ";": ",", "?": ""
    }

    for char, replacement in translations.items():
        text = text.replace(char, replacement)

    return " ".join(text.split())


def update_material_thermal_data(doc, data):
    # 1. Prepare Names
    raw_name = data['material']
    safe_name = sanitize_revit_name(raw_name)
    asset_name = safe_name + "_Thermal"

    print("    [BEM_ENV] Processing: '{}'".format(safe_name))

    # 2. CALCULATION: Manual Unit Conversion (SI -> Imperial)
    # This bypasses UnitUtils entirely, making the script version-proof.
    # ----------------------------------------------------------------
    # Conductivity: W/(m·K) -> BTU/(h·ft·°F) | Factor: ~0.5778
    k_imp = float(data['conductivity']) * 0.577789

    # Density: kg/m³ -> lb/ft³ | Factor: ~0.0624
    d_imp = float(data['density']) * 0.062428

    # Specific Heat: J/(kg·K) -> BTU/(lb·°F) | Factor: ~0.0002388
    cp_imp = float(data['specificheat']) * 0.000238846

    # Safety Guards (Revit crashes on 0.0 or negative thermal values)
    k_imp = max(0.001, k_imp)
    d_imp = max(0.001, d_imp)
    cp_imp = max(0.001, cp_imp)

    # 3. Find or Create Material
    material = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material)
                     if m.Name == safe_name), None)

    if not material:
        mat_id = DB.Material.Create(doc, safe_name)
        material = doc.GetElement(mat_id)

    # 4. Manage Thermal Asset (Optimized Flow)
    asset_id = material.ThermalAssetId

    try:
        if asset_id == DB.ElementId.InvalidElementId:
            # --- CASE A: CREATE NEW ---
            # Create the object in memory
            thermal_asset = DB.ThermalAsset(asset_name, DB.ThermalMaterialType.Solid)

            # SET PROPERTIES BEFORE CREATING THE ELEMENT
            # This prevents the "Internal Error" caused by modifying a fresh element too fast
            thermal_asset.ThermalConductivity = k_imp
            thermal_asset.Density = d_imp
            thermal_asset.SpecificHeat = cp_imp

            # Commit to Revit Database
            pse_id = DB.PropertySetElement.Create(doc, thermal_asset)
            material.ThermalAssetId = pse_id
            print("    [BEM_ENV] Created New Asset: K={:.4f}, D={:.4f}, Cp={:.4f}".format(k_imp, d_imp, cp_imp))

        else:
            # --- CASE B: UPDATE EXISTING ---
            pse = doc.GetElement(asset_id)
            asset = pse.GetThermalAsset()

            # Update values
            asset.ThermalConductivity = k_imp
            asset.Density = d_imp
            asset.SpecificHeat = cp_imp

            # Commit update
            pse.SetThermalAsset(asset)
            print("    [BEM_ENV] Updated Asset: K={:.4f}, D={:.4f}, Cp={:.4f}".format(k_imp, d_imp, cp_imp))

        return material.Id

    except Exception as e:
        print("    [BEM_ENV_ERROR] Failed on values (Imp): K={}, D={}, Cp={}".format(k_imp, d_imp, cp_imp))
        print("    [BEM_ENV_ERROR] Exception: {}".format(e))
        return material.Id