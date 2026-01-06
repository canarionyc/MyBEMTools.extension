# -*- coding: utf-8 -*-
import clr
import sys
import re
import json
import os

# Add Revit API References
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
from Autodesk.Revit.DB import *
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

# Set the document
doc = DocumentManager.Instance.CurrentDBDocument

# ============================================================================
# CONFIGURATION
# ============================================================================
JSON_PATH = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\materials.json"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_material_name(raw_name):
    """
    Fixes encoding and applies the 'a < d < b' -> 'd entre a y b' rule.
    """
    if not raw_name: return "Material_Sin_Nombre"

    # 1. Fix encoding/accents (Ensure we are working with unicode)
    # IronPython 2.7 string handling can be tricky with JSON.
    # Usually simple assignment works if the file is read correctly.
    clean = raw_name

    # 2. Apply Rule: "750 < d < 900" becomes "d entre 750 y 900"
    # Regex explains: Look for number, space?, <, space?, d, space?, <, space?, number
    pattern = r"(\d+)\s*<\s*d\s*<\s*(\d+)"
    replacement = r"d entre \1 y \2"

    clean = re.sub(pattern, replacement, clean)

    return clean


def get_or_create_material(doc, name):
    """
    Finds a material by name or creates it.
    Returns the Material element.
    """
    # Try to find existing
    collector = FilteredElementCollector(doc).OfClass(Material)
    for mat in collector:
        if mat.Name == name:
            return mat

    # If not found, create new
    new_id = Material.Create(doc, name)
    return doc.GetElement(new_id)


def set_param(elem, built_in_param, value):
    """Safe parameter setter"""
    p = elem.get_Parameter(built_in_param)
    if p and value is not None:
        # Convert numbers to string for text params
        if isinstance(value, float):
            p.Set(str(value))
        else:
            p.Set(str(value))


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    if not os.path.exists(JSON_PATH):
        return "Error: File not found at {}".format(JSON_PATH)

    # Read JSON
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)

    # Start Transaction
    TransactionManager.Instance.EnsureInTransaction(doc)

    report = []

    try:
        for item in data:
            raw_name = item.get('name', 'Unnamed')
            props = item.get('properties', {})

            # 1. Clean the name
            final_name = clean_material_name(raw_name)

            # 2. Get or Create (The "Upsert")
            mat = get_or_create_material(doc, final_name)

            # 3. Update Identity Data
            # Map "group" from JSON to Revit "Class"
            group = item.get('group', 'General')
            set_param(mat, BuiltInParameter.MATERIAL_PARAM_CLASS, group)

            # Map "conductivity" to "Model" (for Schedules)
            k_val = props.get('conductivity', 0)
            set_param(mat, BuiltInParameter.ALL_MODEL_MODEL, k_val)

            # Map "density" to "Description"
            d_val = props.get('density', 0)
            desc_str = "Density: {} kg/m3".format(d_val)
            set_param(mat, BuiltInParameter.ALL_MODEL_DESCRIPTION, desc_str)

            # Map "specific_heat" to "Comments"
            cp_val = props.get('specific_heat', 0)
            comment_str = "Cp: {} J/kgK".format(cp_val)
            set_param(mat, BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS, comment_str)

            report.append("Processed: {}".format(final_name))

        TransactionManager.Instance.TransactionTaskDone()
        return "Success. Processed {} materials.".format(len(report))

    except Exception as e:
        TransactionManager.Instance.ForceCloseTransaction()
        return "Error: {}".format(str(e))


# Run the script
if __name__ == "__main__":
    result = main()
    print(result)  # Or OUT = result in Dynamo