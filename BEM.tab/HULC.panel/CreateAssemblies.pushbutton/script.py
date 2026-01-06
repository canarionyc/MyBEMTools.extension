# -*- coding: utf-8 -*-
"""
Create HULC Assemblies - OBSESSIVE LOGGER EDITION
"""
__title__ = "Create HULC\nAssemblies"
__author__ = "BEM Tools"

import os
import re
import json
import unicodedata
from collections import defaultdict

# pyRevit imports
from pyrevit import revit, forms, script
import Autodesk.Revit.DB as DB

# ============================================================================
# 0. FORCE OUTPUT WINDOW OPEN
# ============================================================================
output = script.get_output()
output.close()  # Clear previous
output.show()  # FORCE SHOW
print("--- INITIALIZING SCRIPT ---")


def log(msg):
    """Unconditional printer."""
    print(msg)


def log_step(step, msg):
    print("\n[STEP {}] {}".format(step, msg))


def log_detail(key, val):
    print("   > {}: {}".format(key, val))


# ============================================================================
# CONFIGURATION
# ============================================================================
DEFAULT_JSON_PATH = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\bem_update_package.json"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def meters_to_internal(value_in_meters):
    # Revit 2021+ Unit handling
    return DB.UnitUtils.ConvertToInternalUnits(value_in_meters, DB.UnitTypeId.Meters)


def sanitize_revit_name(text):
    if not text: return "Unnamed_Material"
    if not isinstance(text, unicode):
        text = unicode(text, 'utf-8') if isinstance(text, str) else unicode(text)
    nfkd = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in nfkd if not unicodedata.combining(c)])
    translations = {"<": "inf", ">": "sup", "[": "(", "]": ")", "{": "(", "}": ")", "|": "-", ";": ",", "?": "",
                    ":": "-", "/": "-"}
    for char, rep in translations.items():
        text = text.replace(char, rep)
    return " ".join(text.split())


def process_hulc_name(raw_name):
    if not raw_name: return "Material_Sin_Nombre"
    clean = raw_name
    pattern = r"([\d\.]+)\s*<\s*d\s*<\s*([\d\.]+)"
    replacement = r"d entre \1 y \2"
    clean = re.sub(pattern, replacement, clean)
    return sanitize_revit_name(clean)


def get_material_id(doc, raw_name):
    target_name = process_hulc_name(raw_name)
    # log_detail("Looking for Material", target_name) # Very verbose
    mat = DB.FilteredElementCollector(doc).OfClass(DB.Material) \
        .Where(lambda m: m.Name == target_name).FirstElement()
    if mat: return mat.Id

    log_detail("WARNING", "Material NOT FOUND: '{}'".format(target_name))
    return DB.ElementId.InvalidElementId


def get_template_type(doc, category_name):
    log_detail("Template Search", "Category: {}".format(category_name))

    bic = None
    if category_name == "OST_Walls":
        bic = DB.BuiltInCategory.OST_Walls
        sys_class = DB.WallType
    elif category_name == "OST_Floors":
        bic = DB.BuiltInCategory.OST_Floors
        sys_class = DB.FloorType
    elif category_name == "OST_Roofs":
        bic = DB.BuiltInCategory.OST_Roofs
        sys_class = DB.RoofType
    elif category_name == "OST_StructuralFoundation":
        bic = DB.BuiltInCategory.OST_StructuralFoundation
        sys_class = DB.FloorType
    else:
        log_detail("ERROR", "Unknown Category: {}".format(category_name))
        return None, None

    col = DB.FilteredElementCollector(doc).OfCategory(bic).WhereElementIsElementType()
    valid_types = [e for e in col if isinstance(e, sys_class)]

    if not valid_types:
        log_detail("ERROR", "No types found in project for category.")
        return None, None

    # Priority Search
    for t in valid_types:
        if "generic" in t.Name.lower() or "genérico" in t.Name.lower():
            log_detail("Found Template", t.Name)
            return t, sys_class

    fallback = valid_types[0]
    log_detail("Fallback Template", fallback.Name)
    return fallback, sys_class


# ============================================================================
# MAIN
# ============================================================================
def main():
    log_step(1, "CHECKING FILE PATH")
    json_path = DEFAULT_JSON_PATH

    if os.path.exists(json_path):
        log_detail("Status", "File Found")
        log_detail("Path", json_path)
    else:
        log_detail("Status", "FILE MISSING at default path")
        json_path = forms.pick_file(file_ext='json', title="Select BEM Update Package")
        if not json_path:
            log("USER CANCELLED. EXITING.")
            return

    log_step(2, "READING JSON")
    try:
        with open(json_path, 'r') as f:
            raw_data = json.load(f)
        log_detail("Row Count", len(raw_data))
        if len(raw_data) > 0:
            log_detail("First Item Keys", raw_data[0].keys())
    except Exception as e:
        log("!!! FATAL ERROR READING JSON !!!")
        log(str(e))
        return

    log_step(3, "GROUPING ASSEMBLIES")
    assemblies = defaultdict(list)
    for row in raw_data:
        if 'assembly' in row:
            assemblies[row['assembly']].append(row)
        else:
            log("SKIP: Row missing 'assembly' key")

    log_detail("Unique Assemblies Found", len(assemblies))
    if len(assemblies) == 0:
        log("!!! NO ASSEMBLIES FOUND. EXITING. !!!")
        return

    log_step(4, "STARTING TRANSACTION")
    doc = revit.doc
    t = DB.Transaction(doc, "Create HULC Assemblies")
    t.Start()

    try:
        count = 0
        for asm_name, layers in assemblies.items():
            print("-" * 50)
            log("PROCESSING: {}".format(asm_name))

            # 1. Category
            cat_str = layers[0].get('revit_category', 'OST_Walls')
            log_detail("Category", cat_str)

            # 2. Template
            template, sys_class = get_template_type(doc, cat_str)
            if not template:
                log("SKIP: Could not find template.")
                continue

            # 3. Get/Create
            target_type = None
            col = DB.FilteredElementCollector(doc).OfClass(sys_class)
            for e in col:
                if e.Name == asm_name:
                    target_type = e
                    log_detail("Action", "Updating existing type")
                    break

            if not target_type:
                try:
                    target_type = template.Duplicate(asm_name)
                    log_detail("Action", "Created NEW type")
                except Exception as e:
                    log_detail("ERROR", "Duplicate failed: " + str(e))
                    continue

            # 4. Layers
            try:
                # Dummy start
                dummy_w = meters_to_internal(0.1)
                cs = DB.CompoundStructure.CreateSingleLayerCompoundStructure(
                    dummy_w, DB.MaterialFunctionAssignment.Structure, DB.ElementId.InvalidElementId
                )

                new_layers = []
                log_detail("Layers to build", len(layers))

                for i, layer in enumerate(layers):
                    th_m = layer.get('thickness', 0.1)
                    mat_name = layer.get('material_name', 'Unknown')

                    if th_m < 0.001: th_m = 0.001

                    # Convert
                    w_int = meters_to_internal(th_m)
                    m_id = get_material_id(doc, mat_name)

                    # Log if invalid
                    if m_id == DB.ElementId.InvalidElementId:
                        log("   ! Layer {}: Material '{}' invalid.".format(i, mat_name))

                    cs_layer = DB.CompoundStructureLayer(w_int, DB.MaterialFunctionAssignment.Structure, m_id)
                    new_layers.append(cs_layer)

                cs.SetLayers(new_layers)
                target_type.SetCompoundStructure(cs)
                log("   > Structure Updated.")
                count += 1

            except Exception as e:
                log("   !!! ERROR SETTING LAYERS: " + str(e))

        log_step(5, "FINISHING")
        t.Commit()
        log("TRANSACTION COMMITTED.")
        log("TOTAL PROCESSED: {}".format(count))

        output.center()  # Keep window open

    except Exception as e:
        t.RollBack()
        log("!!! CRITICAL TRANSACTION FAILURE !!!")
        log(str(e))


if __name__ == "__main__":
    main()