#! python3
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
import json
import re
# from pyrevit import script
#
# output = script.get_output()
# output.print_md("# 🛠️ STEP 1: Data Prep (Natural Spanish)")

# --- CONFIGURATION ---
DB_PATH = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\hulc_data.sqlite"
JSON_OUTPUT = os.path.join(os.path.dirname(DB_PATH), "bem_update_package.json")


def sanitize_name(text):
    if not text: return "Material_Sin_Nombre"

    # 1. PRESERVE ACCENTS: We no longer normalize unicode to ASCII
    # text = unicodedata.normalize('NFKD', str(text)) <--- REMOVED

    clean = str(text)

    # 2. SMART REPLACEMENT: "2000 < d < 2300" -> "d entre 2000 y 2300"
    # Regex looks for: Number + < + Letter + < + Number
    pattern = r"(\d+)\s*[<]\s*([a-zA-Z])\s*[<]\s*(\d+)"
    clean = re.sub(pattern, r"\2 entre \1 y \3", clean)

    # 3. Handle remaining forbidden characters in Revit
    # Revit forbids: \ : { } [ ] | ; < > ? ` ~
    # We replace them with readable equivalents or spaces
    replacements = {
        "<": " menor ",
        ">": " mayor ",
        "[": "(", "]": ")",
        "{": "(", "}": ")",
        "|": "-",
        ";": ",",
        "?": "",
        ":": "-",
        "/": "-"
    }

    for old, new in replacements.items():
        clean = clean.replace(old, new)

    # 4. Clean up double spaces created by replacements
    clean = re.sub(r'\s+', ' ', clean).strip()

    return clean



def run_prep():
    print(">>> Connecting to Database...")
    if not os.path.exists(DB_PATH):
        print("    [ERROR] Database not found.")
        return

    data_package = []

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row

            query = """
                    SELECT wc.name        as assembly_name,
                           wc.material    as raw_material_name,
                           wc.thickness   as thickness_m,
                           m.conductivity as k_si,
                           m.density      as d_si,
                           m.specificheat as cp_si
                    FROM wallcons_long wc, \
                         materials m
                    WHERE wc.name = 'FOR INT AC-NH' \
                      AND wc.material = m.name
                    ORDER BY wc.rowid; \
                    """
            print("    [QUERY] {}".format(query))

            rows = conn.execute(query).fetchall()
            print("    [DATA] Fetched {} rows.".format(len(rows)))

            for row in rows:
                print(row)
                safe_name = sanitize_name(row['raw_material_name'])

                item = {
                    "assembly": row['assembly_name'],
                    "material_name": safe_name,
                    "asset_name": safe_name + "_Termico",  # Spanish suffix
                    "properties_si": {
                        "k": float(row['k_si']),
                        "d": float(row['d_si']),
                        "cp": float(row['cp_si']),
                        "thickness": float(row['thickness_m'])
                    }
                }
                data_package.append(item)

        # Ensure ensure_ascii=False so accents are written literally to JSON
        with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(data_package, f, indent=4, ensure_ascii=False)

        print("\n>>> SUCCESS")
        print("    Data saved to: {}".format(JSON_OUTPUT))
        # output.print_md("### ✅ Ready for Step 2")

    except Exception as e:
        print("    [CRITICAL ERROR] {}".format(e))


if __name__ == "__main__":
    run_prep()