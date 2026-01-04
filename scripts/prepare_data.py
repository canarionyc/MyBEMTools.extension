#! python3
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
import json
import re

# --- CONFIGURATION ---
DB_PATH = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\hulc_data.sqlite"
JSON_OUTPUT = os.path.join(os.path.dirname(DB_PATH), "bem_update_package.json")


def sanitize_name(text):
    if not text: return "Material_Sin_Nombre"
    clean = str(text)

    # Smart Replacement: "2000 < d < 2300" -> "d entre 2000 y 2300"
    pattern = r"(\d+)\s*[<]\s*([a-zA-Z])\s*[<]\s*(\d+)"
    clean = re.sub(pattern, r"\2 entre \1 y \3", clean)

    replacements = {
        "<": " menor ", ">": " mayor ", "[": "(", "]": ")",
        "{": "(", "}": ")", "|": "-", ";": ",", "?": "", ":": "-", "/": "-"
    }
    for old, new in replacements.items():
        clean = clean.replace(old, new)

    return re.sub(r'\s+', ' ', clean).strip()


def safe_float(value, default=None):
    """
    Prevents the 'float() argument must be a string or a number' crash.
    Returns 'default' if the database value is None or empty.
    """
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def run_prep():
    print(">>> Connecting to Database...")
    if not os.path.exists(DB_PATH):
        print("    [ERROR] Database not found.")
        return

    data_package = []

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row

            # Query includes 'resistance' for air gap calculation
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
                    WHERE wc.name = 'FOR INT AC-NH'
                    ORDER BY wc.rowid; \
                    """

            rows = conn.execute(query).fetchall()
            print("    [DATA] Fetched {} rows.".format(len(rows)))

            for row in rows:
                safe_name = sanitize_name(row['raw_material_name'])
                group_name = sanitize_name(row['material_group']) if row['material_group'] else "Generic"

                # --- SAFELY EXTRACT VALUES ---
                th_val = safe_float(row['thickness_m'], 0.0)
                k_val = safe_float(row['k_si'])
                d_val = safe_float(row['d_si'])
                cp_val = safe_float(row['cp_si'])
                r_val = safe_float(row['r_si'])

                # --- NULL HANDLING LOGIC ---
                # 1. Handle Missing Conductivity (Air Gaps)
                if k_val is None:
                    if r_val is not None and r_val > 0:
                        # Calculate Equivalent k = Thickness / Resistance
                        # W/mK = m / (m²K/W)
                        k_val = th_val / r_val
                        print("    [CALC] Fixed Air Gap '{}': k={:.4f} (Derived from R={})".format(safe_name, k_val,
                                                                                                   r_val))
                    else:
                        k_val = 0.001  # Absolute fallback
                        print("    [WARN] No K or R found for '{}'. Defaulting to 0.001".format(safe_name))

                # 2. Handle Missing Density/Specific Heat (Air Gaps)
                if d_val is None:
                    d_val = 1.2  # Standard Air Density
                if cp_val is None:
                    cp_val = 1005  # Standard Air Specific Heat

                item = {
                    "assembly": row['assembly_name'],
                    "material_name": safe_name,
                    "material_class": group_name,  # <--- We send this to Step 2
                    "asset_name": safe_name + "_Termico",
                    "properties_si": {
                        "k": k_val,
                        "d": d_val,
                        "cp": cp_val,
                        "thickness": th_val
                    }
                }
                data_package.append(item)

        with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(data_package, f, indent=4, ensure_ascii=False)

        print("\n>>> SUCCESS")
        print("    Data saved to: {}".format(JSON_OUTPUT))

    except Exception as e:
        print("    [CRITICAL ERROR] {}".format(e))


if __name__ == "__main__":
    run_prep()