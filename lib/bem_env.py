# -*- coding: utf-8 -*-
import sys
import os
import unicodedata
import logging
# noinspection PyUnresolvedReferences
from Autodesk.Revit import DB

# --- ENVIRONMENT SETUP ---
# Ensure flush exists (Fixes the "ScriptIO" error)
if not hasattr(sys.stdout, 'flush'):
    sys.stdout.flush = lambda: None

# --- CONSTANTS ---
db_path = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\hulc_data.sqlite"


# --- HELPER FUNCTIONS ---
def sanitize_revit_name(text):
    """
    1. Removes Accents (Hormigón -> Hormigon)
    2. Replaces prohibited characters
    3. Trims whitespace
    """
    if not text:
        return "Unnamed_Material"

    nfkd_form = unicodedata.normalize('NFKD', str(text))
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    translations = {
        "<": "inf", ">": "sup",
        "[": "(", "]": ")",
        "{": "(", "}": ")",
        "|": "-", ";": ",", "?": ""
    }

    for char, replacement in translations.items():
        text = text.replace(char, replacement)

    return " ".join(text.split())


def update_material_thermal_data(doc, data):
    # 1. Prepare Names
    raw_name = data['material']
    safe_name = sanitize_revit_name(raw_name)

    print("    [BEM_ENV] Processing: '{}'".format(safe_name))

    # 2. Find or Create Material
    material = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material)
                     if m.Name == safe_name), None)

    if not material:
        mat_id = DB.Material.Create(doc, safe_name)
        material = doc.GetElement(mat_id)

    # 3. Manage Thermal Asset
    asset_id = material.ThermalAssetId
    pse = None

    if asset_id == DB.ElementId.InvalidElementId:
        # Create new Asset
        asset_name = safe_name + "_Thermal"
        thermal_asset = DB.ThermalAsset(asset_name, DB.ThermalMaterialType.Solid)
        pse_id = DB.PropertySetElement.Create(doc, thermal_asset)
        pse = doc.GetElement(pse_id)
        material.ThermalAssetId = pse_id
    else:
        # Edit existing
        pse = doc.GetElement(asset_id)

    # 4. UNIT CONVERSION (Corrected)
    # ---------------------------------------------------
    val_k_si = float(data['conductivity'])  # W/(m·K)
    val_d_si = float(data['density'])  # kg/m³
    val_cp_si = float(data['specificheat'])  # J/(kg·K)

    # CORRECTED UNIT IDENTIFIERS:
    # Specific Heat uses Celsius in Revit API naming convention
    k_internal = DB.UnitUtils.ConvertToInternalUnits(val_k_si, DB.UnitTypeId.WattsPerMeterKelvin)
    d_internal = DB.UnitUtils.ConvertToInternalUnits(val_d_si, DB.UnitTypeId.KilogramsPerCubicMeter)
    cp_internal = DB.UnitUtils.ConvertToInternalUnits(val_cp_si,
                                                      DB.UnitTypeId.JoulesPerKilogramCelsius)  # <--- FIXED HERE

    # 5. Apply Values
    asset = pse.GetThermalAsset()

    # Guard against absolute zeros
    asset.ThermalConductivity = max(0.0001, k_internal)
    asset.Density = max(0.0001, d_internal)
    asset.SpecificHeat = max(0.0001, cp_internal)

    try:
        pse.SetThermalAsset(asset)
        return material.Id
    except Exception as e:
        print("    [BEM_ENV_ERROR] Failed to set properties for {}: {}".format(safe_name, e))
        return material.Id