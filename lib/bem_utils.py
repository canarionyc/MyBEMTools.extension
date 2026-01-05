# -*- coding: utf-8 -*-
import sys
import logging
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


# Setup a standard BEM logger for the whole project
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s: %(message)s',
                    stream=sys.stdout  # <--- THIS IS THE KEY FOR PYREVIT
)
logger = logging.getLogger('BEM_Project')


# --- 1. THE FULL UNIT DUMPER ---
def dump_all_units():
    print(">>> 📚 Generating Unit Reference File...")
    valid_units = []
    try:
        for name in dir(DB.UnitTypeId):
            if not name.startswith("__"):
                valid_units.append(name)
    except Exception as e:
        print("    [ERROR] Could not scan library: {}".format(e))
        return

    try:
        # Use io.open here too for safety
        with io.open(UNIT_DUMP_FILE, 'w', encoding='utf-8') as f:
            f.write(u"REVIT API UNIT DUMP\n")
            f.write(u"===================\n")
            f.write(u"Total Count: {}\n\n".format(len(valid_units)))
            for u in sorted(valid_units):
                f.write(u"DB.UnitTypeId.{}\n".format(u))

        print("    [INFO] Saved {} units to:".format(len(valid_units)))
        print("           {}".format(UNIT_DUMP_FILE))
        output.print_md("> 📄 **Unit List Saved:** `revit_units_dump.txt`")
    except Exception as e:
        print("    [WARNING] File write failed: {}".format(e))


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