#! python3
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
import importlib
import gc  # <--- CRITICAL: Garbage Collector interface

from pyrevit import revit, DB, script

# Force a reload of bem_env so changes apply without restarting Revit
import bem_env

importlib.reload(bem_env)
from bem_env import update_material_thermal_data, db_path

# --- OUTPUT SETUP ---
output = script.get_output()
output.print_md("# BEM SYNC: Obsessive Progress Log (Safe Mode)")


def run_safe_sync():
    print(">>> STEP 1: Initializing Environment...")
    doc = revit.doc
    t = None  # Initialize variable to avoid 'UnboundLocalError' in finally block

    try:
        # --- STEP 2: DATABASE ---
        print("\n>>> STEP 2: Connecting to BEM Database...")
        if not os.path.exists(db_path):
            print("    [ERROR] Database not found at: {}".format(db_path))
            return

        # Use 'with' context manager for SQLite (Prevents file locking)
        db_layers = []
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            print("    [INFO] Connected to: {}".format(os.path.basename(db_path)))

            # Your exact query
            query = """
                    SELECT wc.name,
                           wc.material,
                           m.material_group,
                           round(wc.thickness, 4)   as thickness,
                           round(m.conductivity, 4) as conductivity,
                           round(m.density, 4)      as density,
                           round(m.specificheat, 4) as specificheat
                    FROM wallcons_long wc, \
                         materials m
                    WHERE wc.name = 'SOL CAM SANIT' \
                      AND wc.material = m.name
                    ORDER BY wc.rowid; \
                    """
            db_layers = conn.execute(query).fetchall()

        if not db_layers:
            print("    [WARNING] No data found in DB for 'SOL CAM SANIT'.")
            return

        print("    [DATA] Found {} layers.".format(len(db_layers)))

        # --- STEP 3: REVIT TRANSACTION ---
        print("\n>>> STEP 3: Initializing Revit Transaction...")

        # Manual Transaction Handling
        t = DB.Transaction(doc, "BEM: Sync SOL CAM SANIT")
        t.Start()
        print("    [STATUS] Transaction Started.")

        # Find Target Type
        target_name = "SOL CAM SANIT"
        target_type = None

        # Safe Search
        for ft in DB.FilteredElementCollector(doc).OfClass(DB.FloorType):
            p = ft.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
            if p and p.AsString() == target_name:
                target_type = ft
                break

        if not target_type:
            print("    [ERROR] FloorType '{}' not found.".format(target_name))
            t.RollBack()
            return

        # Update Layers
        struct = target_type.GetCompoundStructure()
        revit_layer_count = struct.LayerCount

        for i, row in enumerate(db_layers):
            print("\n    --- Processing Layer {} ---".format(i))

            if i >= revit_layer_count:
                print("    [SKIP] Index {} exceeds Revit layers.".format(i))
                continue

            # Call logic from bem_env (Unit conversions & Asset creation)
            mat_id = update_material_thermal_data(doc, row)

            # Update Thickness (Meters -> Feet)
            thickness_ft = float(row['thickness']) / 0.3048
            print("    [REVIT] Setting Material & Thickness ({} ft)".format(round(thickness_ft, 4)))

            struct.SetMaterialId(i, mat_id)
            struct.SetLayerWidth(i, thickness_ft)

        # Apply Structure
        target_type.SetCompoundStructure(struct)

        # Commit
        t.Commit()
        print("    [SUCCESS] Transaction Committed.")
        output.print_md("### SUCCESS: SOL CAM SANIT Updated")

    except Exception as e:
        print("\n    [CRITICAL FAILURE]: {}".format(str(e)))
        if t and t.GetStatus() == DB.TransactionStatus.Started:
            t.RollBack()
            print("    [SAFETY] Transaction Rolled Back.")

    finally:
        # --- STEP 4: CLEANUP (The fix for Journal Errors) ---
        print("\n>>> STEP 4: Cleanup...")
        if t:
            t.Dispose()
            print("    [SYSTEM] Transaction Disposed.")

        # Force Python to release memory NOW
        del t
        gc.collect()
        print("    [SYSTEM] Garbage Collection Complete.")


if __name__ == "__main__":
    run_safe_sync()