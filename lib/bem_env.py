# -*- coding: utf-8 -*-
import sys
import logging
from pprint import pprint
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import *
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import SpecTypeId
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Architecture import * # This fixes 'Room'

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

db_path = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\hulc_data.sqlite"

# Setup a standard BEM logger for the whole project
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s: %(message)s',
                    stream=sys.stdout  # <--- THIS IS THE KEY FOR PYREVIT
)
logger = logging.getLogger('BEM_Project')


def sanitize_revit_name(text):
    """
    Limpia CUALQUIER carácter que Revit prohíba en nombres de materiales o assets.
    Prohibidos: { } [ ] | ; < > ? ` ~
    """
    if not text:
        return "Unnamed_BEM_Material"
    print(text)
    # Mapeo de caracteres problemáticos a alternativas seguras
    translations = {
        "<": "inf",
        ">": "sup",
        "[": "(",
        "]": ")",
        "{": "(",
        "}": ")",
        "|": "-",
        ";": ",",
        "?": "",
        "`": "",
        "~": ""
    }

    clean_text = text
    for char, replacement in translations.items():
        clean_text = clean_text.replace(char, replacement)
    print(clean_text)

    # Limpiar espacios dobles sobrantes
    ret_val = " ".join(clean_text.split())
    if ret_val != text:
        print("{} -> {}".format(text,clean_text))

    return ret_val

from pyrevit import revit, DB
def update_material_thermal_data(doc, data):
    raw_name = data['material']
    # 1. LIMPIEZA TOTAL DEL NOMBRE
    safe_name = sanitize_revit_name(raw_name)

    # Buscar o crear material con el nombre limpio
    material = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material)
                     if m.Name == safe_name), None)

    if not material:
        mat_id = DB.Material.Create(doc, safe_name)
        material = doc.GetElement(mat_id)

    # 2. NOMBRE DEL ASSET (También debe ser limpio)
    asset_id = material.ThermalAssetId
    if asset_id == DB.ElementId.InvalidElementId:
        # Usamos el nombre ya limpio para el Asset
        asset_name = safe_name + "_Thermal"
        print("Creating thermal asset {} of type {}".format(asset_name, DB.ThermalMaterialType.Solid))
        pse = DB.PropertySetElement.Create(doc, thermal_asset)
        material.ThermalAssetId = pse.Id
    else:
        pse = doc.GetElement(asset_id)

    # 3. ASIGNACIÓN DE VALORES
    asset = pse.GetThermalAsset()
    asset.ThermalConductivity = float(data['conductivity'])
    asset.Density = float(data['density'])
    asset.SpecificHeat = float(data['specificheat'])

    # Este es el punto donde fallaba: ahora el 'asset' tiene un nombre válido
    pse.SetThermalAsset(asset)
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