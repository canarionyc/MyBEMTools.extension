# -*- coding: utf-8 -*-
import sys
import os
import unicodedata
import logging
from pprint import pprint
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import *
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import SpecTypeId
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Architecture import * # This fixes 'Room'

import pyrevit
print("ACTIVE PYREVIT PATH:")
print(os.path.dirname(pyrevit.__file__))

# Ensure flush exists for CPython 3.12 compatibility
if not hasattr(sys.stdout, 'flush'):
    sys.stdout.flush = lambda: None

from pyrevit import revit, DB


# --- BEM Unit Conversions ---
# Revit Internal (ft) -> Meters (m)
FT_TO_M = 0.3048
# Revit Internal (sqft) -> Square Meters (m2)
SQFT_TO_M2 = 0.09290304
# Revit Internal (cuft) -> Cubic Meters (m3)
CUFT_TO_M3 = 0.0283168

# --- BEM Thermal Constants (SI Units: m²K/W) ---
# Interior surface resistance (Heat flow horizontal)
R_SI = 0.13
# Exterior surface resistance (Heat flow horizontal)
R_SE = 0.04

# Setup a standard BEM logger for the whole project
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s: %(message)s',
                    stream=sys.stdout  # <--- THIS IS THE KEY FOR PYREVIT
)
logger = logging.getLogger('BEM_Project')




# Ejemplo de uso:
# 'Hormigón armado 2300 < d < 2500' -> 'Hormigón armado 2300 inf d inf 2500'
# 'Cloruro de polivinilo [PVC]'     -> 'Cloruro de polivinilo (PVC)'

# def get_u_value(wall_type):
#     """Calculates U-Value (W/m²·K). Formula: U = 1/R_total"""
#     r_value = wall_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_FINAL_RVALUE).AsDouble()
#     if r_value > 0:
#         # Convert from Imperial R to Metric U
#         # R_metric = R_imperial * 0.1761
#         return 1.0 / (r_value * 0.1761)
#     return None
#
# def get_readable_units(doc):
#     unit_id = doc.GetUnits().GetFormatOptions(SpecTypeId.Length).GetUnitTypeId()
#     return LabelUtils.GetLabelForUnit(unit_id)
#
# def get_forge_units(doc):
#     """Returns human-readable length units (e.g., 'Meters')"""
#     units = doc.GetUnits()
#     spec_id = SpecTypeId.Length
#     unit_id = units.GetFormatOptions(spec_id).GetUnitTypeId()
#     return LabelUtils.GetLabelForUnit(unit_id)
#
# def get_wall_count(doc):
#     """Basic collector to verify API access"""
#     return FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType().GetElementCount()


# -*- coding: utf-8 -*-
import sys
import unicodedata
from Autodesk.Revit import DB

# --- PATH & CONSTANTS ---
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

    # 4. UNIT CONVERSION (The Fix for the Internal Error)
    # We must convert SI (DB) -> Revit Internal (Imperial)
    # ---------------------------------------------------
    val_k_si = float(data['conductivity'])  # W/(m·K)
    val_d_si = float(data['density'])  # kg/m³
    val_cp_si = float(data['specificheat'])  # J/(kg·K)

    # Use Revit's internal engine to convert
    # Note: Using ForgeTypeId (Revit 2022+) or UnitTypeId

    k_internal = DB.UnitUtils.ConvertToInternalUnits(val_k_si, DB.UnitTypeId.WattsPerMeterKelvin)
    d_internal = DB.UnitUtils.ConvertToInternalUnits(val_d_si, DB.UnitTypeId.KilogramsPerCubicMeter)
    cp_internal = DB.UnitUtils.ConvertToInternalUnits(val_cp_si, DB.UnitTypeId.JoulesPerKilogramKelvin)

    # 5. Apply Values
    asset = pse.GetThermalAsset()

    # Guard against absolute zeros which also crash Revit
    asset.ThermalConductivity = max(0.0001, k_internal)
    asset.Density = max(0.0001, d_internal)
    asset.SpecificHeat = max(0.0001, cp_internal)

    try:
        pse.SetThermalAsset(asset)
        return material.Id
    except Exception as e:
        print("    [BEM_ENV_ERROR] Failed to set properties for {}: {}".format(safe_name, e))
        return material.Id