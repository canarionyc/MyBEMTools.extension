#! python3
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
import json
import unicodedata
# from pyrevit import script
#
# output = script.get_output()
# output.print_md("# 🛠️ STEP 1: Data Preparation")

# --- CONFIGURATION ---
# Hardcoded path for stability, or derive relative to script
DB_PATH = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\hulc_data.sqlite"
JSON_OUTPUT = os.path.join(os.path.dirname(DB_PATH), "bem_update_package.json")


def sanitize_name(text):
    if not text: return "Unnamed_Material"
    nfkd_form = unicodedata.normalize('NFKD', str(text))
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    translations = str.maketrans(
        {"<": "inf", ">": "sup", "[": "(", "]": ")", "{": "(", "}": ")", "|": "-", ";": ",", "?": "", ":": "-",
         "/": "-"})
    return text.translate(translations).strip()


def run_prep():
    print(">>> Connecting to Database...")
    if not os.path.exists(DB_PATH):
        print("    [ERROR] Database not found: {}".format(DB_PATH))
        return

    data_package = []

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            print("    [INFO] Connected to: {}".format(os.path.basename(DB_PATH)))

            # THE QUERY
            query = """
                    SELECT wc.name                  as assembly_name,
                           wc.material              as raw_material_name,
                           round(wc.thickness, 4)   as thickness_m,
                           round(m.conductivity, 4) as k_si,
                           round(m.density, 4)      as d_si,
                           round(m.specificheat, 4) as cp_si
                    FROM wallcons_long wc, \
                         materials m
                    WHERE wc.name = 'SOL CAM SANIT' \
                      AND wc.material = m.name
                    ORDER BY wc.rowid; \
                    """
            rows = conn.execute(query).fetchall()

            print("    [DATA] Fetched {} rows.".format(len(rows)))

            for row in rows:
                # PROCESS DATA HERE (Offline from Revit)
                # 1. Clean Name
                safe_name = sanitize_name(row['raw_material_name'])

                # 2. Pre-Calculate Imperial Units (Avoids DLL Version Conflicts)
                # Conductivity: W/(m·K) -> BTU/(h·ft·°F)
                k_imp = float(row['k_si']) * 0.577789

                # Density: kg/m³ -> lb/ft³
                d_imp = float(row['d_si']) * 0.062428

                # Specific Heat: J/(kg·K) -> BTU/(lb·°F)
                cp_imp = float(row['cp_si']) * 0.000238846

                # Thickness: m -> ft
                th_ft = float(row['thickness_m']) / 0.3048

                # Build the clean object
                item = {
                    "assembly": row['assembly_name'],
                    "material_name": safe_name,
                    "asset_name": safe_name + "_Thermal",
                    "thickness_ft": th_ft,
                    "properties": {
                        "k": max(0.001, k_imp),
                        "d": max(0.001, d_imp),
                        "cp": max(0.001, cp_imp)
                    },
                    "debug_si": {
                        "k": row['k_si'],
                        "d": row['d_si'],
                        "cp": row['cp_si']
                    }
                }
                data_package.append(item)

        # SAVE TO JSON
        with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(data_package, f, indent=4)

        print("\n>>> SUCCESS")
        print("    Data saved to: {}".format(JSON_OUTPUT))
        # output.print_md("### ✅ Ready for Step 2")

    except Exception as e:
        print("    [CRITICAL ERROR] {}".format(e))


if __name__ == "__main__":
    run_prep()