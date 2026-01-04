#! python3
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
import json
import re

# --- CONFIGURATION ---
DB_PATH = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\hulc_data.sqlite"
JSON_OUTPUT = os.path.join(os.path.dirname(DB_PATH), "bem_update_package_FULL.json")


def sanitize_name(text):
    if not text: return "Material_Sin_Nombre"
    clean = str(text)
    pattern = r"(\d+)\s*[<]\s*([a-zA-Z])\s*[<]\s*(\d+)"
    clean = re.sub(pattern, r"\2 entre \1 y \3", clean)
    replacements = {"<": " menor ", ">": " mayor ", "[": "(", "]": ")", "{": "(", "}": ")", "|": "-", ";": ",", "?": "",
                    ":": "-", "/": "-"}
    for old, new in replacements.items():
        clean = clean.replace(old, new)
    return re.sub(r'\s+', ' ', clean).strip()


def safe_float(value, default=None):
    if value is None or value == "": return default
    try:
        return float(value)
    except:
        return default


def run_prep():
    print(">>> Connecting to Database...")
    if not os.path.exists(DB_PATH):
        print("    [ERROR] Database not found.")
        return

    # Dictionary to hold { "AssemblyName": [List of Layers] }
    full_library = {}

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row

            # --- QUERY ALL CONSTRUCTIONS (Removed WHERE clause) ---
            query = """
                    SELECT wc.name        as assembly_name,
                           wc.material    as raw_material_name,
                           wc.thickness   as thickness_m,
                           m.material_group,
                           m.conductivity as k_si,
                           m.density      as d_si,
                           m.specificheat as cp_si,
                           m.resistance   as r_si
                    FROM wallcons_long wc
                             LEFT JOIN materials m ON wc.material = m.name
                    ORDER BY wc.name, wc.rowid; \
                    """

            rows = conn.execute(query).fetchall()
            print("    [DATA] Fetched {} total layers.".format(len(rows)))

            for row in rows:
                assembly = row['assembly_name']
                if assembly not in full_library:
                    full_library[assembly] = []

                safe_mat_name = sanitize_name(row['raw_material_name'])
                group_name = sanitize_name(row['material_group']) if row['material_group'] else "Generic"

                # Math & Fallbacks
                th_val = safe_float(row['thickness_m'], 0.0)
                k_val = safe_float(row['k_si'])
                d_val = safe_float(row['d_si'], 1.0)
                cp_val = safe_float(row['cp_si'], 1000.0)
                r_val = safe_float(row['r_si'])

                # Air Gap Calculation (If K is missing but R exists)
                if k_val is None:
                    if r_val is not None and r_val > 0:
                        k_val = th_val / r_val  # k = d/R
                    else:
                        k_val = 0.001

                item = {
                    "material_name": safe_mat_name,
                    "material_class": group_name,
                    "asset_name": safe_mat_name + "_Termico",
                    "properties_si": {
                        "k": k_val, "d": d_val, "cp": cp_val, "thickness": th_val
                    }
                }
                full_library[assembly].append(item)

        with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(full_library, f, indent=4, ensure_ascii=False)

        print("\n>>> SUCCESS")
        print("    Exported {} unique assemblies.".format(len(full_library)))
        print("    File: {}".format(JSON_OUTPUT))

    except Exception as e:
        print("    [CRITICAL ERROR] {}".format(e))


if __name__ == "__main__":
    run_prep()