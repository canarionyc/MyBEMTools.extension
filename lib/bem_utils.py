# -*- coding: utf-8 -*-
import logging
from Autodesk.Revit.DB import *

# Setup a standard BEM logger for the whole project
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger('BEM_Project')

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
