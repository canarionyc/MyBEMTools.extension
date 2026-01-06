# -*- coding: utf-8 -*-
"""
Imports HULC materials from a JSON file.
Style: Uses the Output Window for the final report (Copy-Paste friendly).
"""
__title__ = "Import HULC\nMaterials"
__author__ = "BEM Tools"

import os
import re
import json
import unicodedata

# pyRevit libraries
from pyrevit import revit, forms, script

# Revit API imports
import Autodesk.Revit.DB as DB

# ============================================================================
# SETUP OUTPUT WINDOW
# ============================================================================
output = script.get_output()
output.close()  # Close any previous windows
output.show()  # Force the window to appear immediately
output.set_title("HULC Import Report")


def log(msg):
    """Prints message to the output window."""
    print(msg)


def log_action(action, details):
    """Formatted action logger."""
    print("   [{}] {}".format(action, details))


# ============================================================================
# SAFE PARAMETER MAPPING
# ============================================================================
class SafeBIP:
    @staticmethod
    def get(name, integer_id):
        try:
            return getattr(DB.BuiltInParameter, name)
        except AttributeError:
            return DB.BuiltInParameter(integer_id)


BIP_CLASS = SafeBIP.get("MATERIAL_PARAM_CLASS", -1002101)
BIP_DESCRIPTION = SafeBIP.get("ALL_MODEL_DESCRIPTION", -1001202)
BIP_COMMENTS = SafeBIP.get("ALL_MODEL_INSTANCE_COMMENTS", -1001205)
BIP_MODEL = SafeBIP.get("ALL_MODEL_MODEL", -1001203)


# ============================================================================
# LOGIC
# ============================================================================
def sanitize_revit_name(text):
    if not text: return "Unnamed_Material"
    if not isinstance(text, unicode):
        text = unicode(text, 'utf-8') if isinstance(text, str) else unicode(text)

    nfkd_form = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    translations = {
        "<": "inf", ">": "sup", "[": "(", "]": ")",
        "{": "(", "}": ")", "|": "-", ";": ",",
        "?": "", ":": "-", "/": "-"
    }
    for char, replacement in translations.items():
        text = text.replace(char, replacement)

    return " ".join(text.split())


def process_hulc_name(raw_name):
    if not raw_name: return "Material_Sin_Nombre"
    clean = raw_name
    pattern = r"([\d\.]+)\s*<\s*d\s*<\s*([\d\.]+)"
    replacement = r"d entre \1 y \2"
    clean = re.sub(pattern, replacement, clean)
    return sanitize_revit_name(clean)


def get_or_create_material(doc, name, local_cache):
    name_lower = name.lower().strip()

    # 1. CHECK LOCAL CACHE
    if name_lower in local_cache:
        log_action("CACHE", "Found '{}' in local cache.".format(name))
        return local_cache[name_lower]

    # 2. CHECK REVIT DB
    collector = DB.FilteredElementCollector(doc).OfClass(DB.Material)
    for mat in collector:
        if mat.Name.lower().strip() == name_lower:
            log_action("FOUND", "Found existing '{}' in Revit.".format(mat.Name))
            local_cache[name_lower] = mat
            return mat

    # 3. CREATE NEW
    try:
        log_action("CREATE", "Creating NEW material: '{}'".format(name))
        new_id = DB.Material.Create(doc, name)
        new_mat = doc.GetElement(new_id)
        local_cache[name_lower] = new_mat
        return new_mat
    except Exception as e:
        if "in use" in str(e) or "exist" in str(e):
            log_action("WARN", "Name collision. Retrying fetch...")
            check_again = DB.FilteredElementCollector(doc).OfClass(DB.Material) \
                .Where(lambda m: m.Name == name).FirstElement()
            if check_again:
                local_cache[name_lower] = check_again
                return check_again
        raise e


def set_param(elem, bip, value):
    p = elem.get_Parameter(bip)
    if p and value is not None:
        p.Set(str(value))


# ============================================================================
# MAIN EXECUTION
# ============================================================================
DEFAULT_JSON_PATH = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\materials.json"
json_path = DEFAULT_JSON_PATH

if not os.path.exists(json_path):
    json_path = forms.pick_file(file_ext='json', title="Select HULC Materials JSON")

if json_path:
    # Read Data
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        log("CRITICAL ERROR: Failed to read JSON file.")
        log(str(e))
        data = None

    if data:
        doc = revit.doc
        material_cache = {}

        log("========================================")
        log("STARTING MATERIAL IMPORT")
        log("File: {}".format(os.path.basename(json_path)))
        log("Items to Process: {}".format(len(data)))
        log("========================================")

        t = DB.Transaction(doc, "Import HULC Materials")
        t.Start()

        try:
            count = 0
            for i, item in enumerate(data):
                raw_name = item.get('name', 'Unnamed')
                log("\n[{}/{}] Processing: {}".format(i + 1, len(data), raw_name))

                final_name = process_hulc_name(raw_name)

                mat = get_or_create_material(doc, final_name, material_cache)

                mat_group = item.get('material_group', 'General')
                k_val = item.get('conductivity', 0.0)
                d_val = item.get('density', 0)
                cp_val = item.get('specificheat', 0)

                set_param(mat, BIP_CLASS, mat_group)
                set_param(mat, BIP_DESCRIPTION, "HULC Import | Density: {} kg/m3".format(d_val))
                set_param(mat, BIP_COMMENTS, "Cp: {} J/kgK".format(cp_val))
                set_param(mat, BIP_MODEL, k_val)

                count += 1

            t.Commit()

            # FINAL REPORT (No pop-up, just big text)
            log("\n" + "=" * 40)
            log("SUCCESS: Processed {} materials.".format(count))
            log("=" * 40)

            # This line ensures the output window stays active
            output.center()

        except Exception as e:
            t.RollBack()
            log("\n" + "!" * 40)
            log("CRITICAL ERROR - TRANSACTION ROLLED BACK")
            log(str(e))
            log("!" * 40)