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

# -*- coding: utf-8 -*-
import sys
import unicodedata
# We use the direct Revit API imports to be safe
from Autodesk.Revit import DB

# --- ENVIRONMENT & PATHS ---
db_path = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\hulc_data.sqlite"


# --- HELPER FUNCTIONS ---
def sanitize_revit_name(text):
    """
    1. Removes Accents (Hormigón -> Hormigon)
    2. Replaces prohibited Revit characters (< > [ ] { } etc)
    3. Trims whitespace
    """
    if not text:
        return "Unnamed_Material"

    # Normalize unicode characters (remove accents)
    nfkd_form = unicodedata.normalize('NFKD', str(text))
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    # Map prohibited characters
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

    print("    [BEM_ENV] Sanitized: '{}' -> '{}'".format(raw_name, safe_name))

    # 2. Find or Create Material
    material = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material)
                     if m.Name == safe_name), None)

    if not material:
        print("    [BEM_ENV] Creating new Material: {}".format(safe_name))
        mat_id = DB.Material.Create(doc, safe_name)
        material = doc.GetElement(mat_id)

    # 3. Manage Thermal Asset (The Critical Part)
    asset_id = material.ThermalAssetId

    if asset_id == DB.ElementId.InvalidElementId:
        # --- CREATION LOGIC ---
        asset_name = safe_name + "_Thermal"
        print("    [BEM_ENV] Creating new ThermalAsset: {}".format(asset_name))

        # DEFINITION (This was likely missing or misspelled in your file)
        thermal_asset = DB.ThermalAsset(asset_name, DB.ThermalMaterialType.Solid)

        # ASSIGNMENT
        pse = DB.PropertySetElement.Create(doc, thermal_asset)
        material.ThermalAssetId = pse.Id
    else:
        # --- EDITING LOGIC ---
        pse = doc.GetElement(asset_id)

    # 4. Update Properties (Guard against Zeros)
    # Revit crashes if Conductivity is 0.0
    k = max(0.001, float(data['conductivity']))
    d = max(0.001, float(data['density']))
    cp = max(0.001, float(data['specificheat']))

    # Get the asset object to edit it
    asset = pse.GetThermalAsset()
    asset.ThermalConductivity = k
    asset.Density = d
    asset.SpecificHeat = cp

    try:
        pse.SetThermalAsset(asset)
        return material.Id
    except Exception as e:
        print("    [BEM_ENV_ERROR] Failed to set Thermal Asset: {}".format(e))
        return material.Id


# Ejemplo de uso:
# 'Hormigón armado 2300 < d < 2500' -> 'Hormigón armado 2300 inf d inf 2500'
# 'Cloruro de polivinilo [PVC]'     -> 'Cloruro de polivinilo (PVC)'

def get_u_value(wall_type):
    """Calculates U-Value (W/m²·K). Formula: U = 1/R_total"""
    r_value = wall_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_FINAL_RVALUE).AsDouble()
    if r_value > 0:
        # Convert from Imperial R to Metric U
        # R_metric = R_imperial * 0.1761
        return 1.0 / (r_value * 0.1761)
    return None

def get_readable_units(doc):
    unit_id = doc.GetUnits().GetFormatOptions(SpecTypeId.Length).GetUnitTypeId()
    return LabelUtils.GetLabelForUnit(unit_id)

def get_forge_units(doc):
    """Returns human-readable length units (e.g., 'Meters')"""
    units = doc.GetUnits()
    spec_id = SpecTypeId.Length
    unit_id = units.GetFormatOptions(spec_id).GetUnitTypeId()
    return LabelUtils.GetLabelForUnit(unit_id)

def get_wall_count(doc):
    """Basic collector to verify API access"""
    return FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType().GetElementCount()