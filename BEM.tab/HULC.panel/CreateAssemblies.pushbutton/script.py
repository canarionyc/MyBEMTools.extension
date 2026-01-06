# -*- coding: utf-8 -*-
import sys
import os
import json
import ast
import re
import io  # <--- REQUIRED FOR ENCODING
import clr

# --- REVIT API SETUP ---
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *

# --- FORCE OUTPUT WINDOW ---
from pyrevit import script

output = script.get_output()
output.close()
output.show()

# --- CONSTANTS ---
JSON_PATH = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\wallcons.json"


# --- HELPER FUNCTIONS ---
def meters_to_internal(val_m):
    return UnitUtils.ConvertToInternalUnits(val_m, UnitTypeId.Meters)


def clean_name(text):
    """
    Basic cleanup. Since we are now reading UTF-8 correctly,
    we don't need to be as aggressive, but we still remove
    Revit-forbidden characters.
    """
    if not text: return "Unnamed"

    # 1. Strip forbidden chars
    # \ : { } [ ] | ; < > ? ` ~
    trans = {
        "\\": "-", ":": "-", "{": "(", "}": ")", "[": "(", "]": ")",
        "|": "-", ";": ",", "<": "inf", ">": "sup", "?": "",
        "/": "-", "*": "x", "\"": "in", "\'": "ft"
    }
    for k, v in trans.items(): text = text.replace(k, v)

    # 2. Whitespace cleanup
    return " ".join(text.split())


def process_material_name(raw):
    # HULC Fix: "d < 1000" -> "d entre..."
    # (Using simple replacement to keep it safe)
    s = str(raw)  # raw is now a proper unicode string thanks to io.open
    s = re.sub(r"([\d\.]+)\s*<\s*d\s*<\s*([\d\.]+)", r"d \1-\2", s)
    return clean_name(s)


# --- MAIN LOGIC ---
def run():
    doc = __revit__.ActiveUIDocument.Document
    print("--- STARTING IMPORT ---")
    print("File: " + JSON_PATH)

    if not os.path.exists(JSON_PATH):
        print("❌ CRITICAL: File not found.")
        return

    # --- 1. READ JSON WITH EXPLICIT ENCODING ---
    try:
        # io.open is crucial for IronPython to handle UTF-8 correctly
        with io.open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print("❌ CRITICAL: JSON Load Error (Encoding?): " + str(e))
        return

    print("Rows found: {}".format(len(data)))

    t = Transaction(doc, "Create HULC Assemblies")
    t.Start()

    count_ok = 0

    for i, row in enumerate(data):
        try:
            # Name should now be clean unicode
            raw_name = row.get('name', 'Assembly_' + str(i))
            asm_name = clean_name(raw_name)

            # --- CATEGORY ---
            cat_str = row.get('revit_category', 'OST_Walls')
            if cat_str == "OST_Walls":
                bic, cls = BuiltInCategory.OST_Walls, WallType
            elif cat_str == "OST_Floors":
                bic, cls = BuiltInCategory.OST_Floors, FloorType
            elif cat_str == "OST_Roofs":
                bic, cls = BuiltInCategory.OST_Roofs, RoofType
            elif cat_str == "OST_StructuralFoundation":
                bic, cls = BuiltInCategory.OST_StructuralFoundation, FloorType
            else:
                print("Skipping unknown category: " + cat_str)
                continue

            # --- LAYERS ---
            # ast.literal_eval handles the "['A','B']" strings
            # We encode to str because ast sometimes dislikes unicode in Py2
            try:
                mat_str = str(row.get('material', '[]'))
                thk_str = str(row.get('thickness', '[]'))
                raw_mats = ast.literal_eval(mat_str)
                raw_thks = ast.literal_eval(thk_str)
            except Exception as e:
                print("⚠️ List parse error on '{}': {}".format(asm_name, e))
                continue

            # --- GET/CREATE TYPE ---
            col = FilteredElementCollector(doc).OfCategory(bic).WhereElementIsElementType()
            target_type = None

            # 1. Exact Match
            for e in col:
                if e.Name == asm_name:
                    target_type = e
                    break

            # 2. Duplicate
            if not target_type:
                # Find Template
                template = None
                for e in col:
                    if isinstance(e, cls):
                        if cls == WallType and e.Kind != WallKind.Basic: continue
                        if "generic" in e.Name.lower() or "generico" in e.Name.lower():
                            template = e
                            break
                if not template:
                    # Fallback
                    for e in col:
                        if isinstance(e, cls):
                            if cls == WallType and e.Kind != WallKind.Basic: continue
                            template = e
                            break

                if not template:
                    print("❌ No template for: " + asm_name)
                    continue

                try:
                    target_type = template.Duplicate(asm_name)
                except Exception as e_dup:
                    print("⚠️ Name collision '{}'. Retrying with suffix...".format(asm_name))
                    target_type = template.Duplicate(asm_name + "_Import")

            # --- BUILD STRUCTURE ---
            dummy_w = meters_to_internal(0.1)
            cs = CompoundStructure.CreateSingleLayerCompoundStructure(
                dummy_w, MaterialFunctionAssignment.Structure, ElementId.InvalidElementId
            )

            new_layers = []
            for m_raw, t_raw in zip(raw_mats, raw_thks):
                th_m = float(t_raw)
                if th_m < 0.002: th_m = 0.002
                w_int = meters_to_internal(th_m)

                # Process Material Name
                mat_clean = process_material_name(m_raw)
                mat_id = ElementId.InvalidElementId

                # Find Material (Name Search)
                mat_col = FilteredElementCollector(doc).OfClass(Material)
                for m in mat_col:
                    if m.Name == mat_clean:
                        mat_id = m.Id
                        break

                # If not found exact, try relaxed search
                if mat_id == ElementId.InvalidElementId:
                    for m in mat_col:
                        if mat_clean in m.Name:  # Substring match
                            mat_id = m.Id
                            break

                lyr = CompoundStructureLayer(w_int, MaterialFunctionAssignment.Structure, mat_id)
                new_layers.append(lyr)

            cs.SetLayers(new_layers)
            target_type.SetCompoundStructure(cs)

            # Tag
            p = target_type.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION)
            if p: p.Set("HULC Import")

            count_ok += 1
            print("OK: " + asm_name)

        except Exception as inner_e:
            print("❌ Error processing {}: {}".format(row.get('name'), inner_e))

    t.Commit()
    print("-" * 30)
    print("FINISHED. Processed: {}".format(count_ok))


run()