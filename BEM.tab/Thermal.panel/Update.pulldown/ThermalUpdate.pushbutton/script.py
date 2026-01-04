#! python3
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
import importlib
import gc
from pyrevit import DB, script

# Force reload of bem_env so you don't have to restart Revit
import bem_env

importlib.reload(bem_env)
from bem_env import update_material_thermal_data, db_path

output = script.get_output()
output.print_md("# BEM SYNC: Obsessive Progress Log (Crash-Proof)")


def run_safe_sync():
    # 1. GET DOC SAFELY
    # Using __revit__ avoids some caching issues
    uidoc = __revit__.ActiveUIDocument
    if not uidoc:
        print("[ERROR] No Active Document.")
        return
    doc = uidoc.Document

    print(">>> STEP 1: Environment Initialized.")

    t = None

    try:
        # --- STEP 2: DATABASE ---
        if not os.path.exists(db_path):
            print("    [ERROR] Database not found: {}".format(db_path))
            return

        db_layers = []
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = """
                    SELECT wc.name, \
                           wc.material, \
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
            print("    [WARNING] No data found in DB.")
            return

        # --- STEP 3: TRANSACTION ---
        print(">>> STEP 2: Starting Transaction...")
        t = DB.Transaction(doc, "BEM: Sync SOL CAM SANIT")
        t.Start()

        # Search for FloorType
        target_name = "SOL CAM SANIT"
        target_type = None

        # Use a localized collector to avoid memory leaks
        col = DB.FilteredElementCollector(doc).OfClass(DB.FloorType)
        for ft in col:
            p = ft.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
            if p and p.AsString() == target_name:
                target_type = ft
                break
        del col  # Release memory

        if not target_type:
            print("    [ERROR] FloorType '{}' not found.".format(target_name))
            t.RollBack()
            return

        # Update Logic
        struct = target_type.GetCompoundStructure()
        for i, row in enumerate(db_layers):
            if i < struct.LayerCount:
                # bem_env handles units and null checks
                mat_id = update_material_thermal_data(doc, row)

                # Update Thickness (Meters -> Feet)
                thickness_ft = float(row['thickness']) / 0.3048

                struct.SetMaterialId(i, mat_id)
                struct.SetLayerWidth(i, thickness_ft)
                print("    > Layer {}: Updated ({})".format(i, row['material']))

        target_type.SetCompoundStructure(struct)

        t.Commit()
        output.print_md("### SUCCESS: Transaction Committed")

    except Exception as e:
        print("\n[CRITICAL FAILURE]: {}".format(str(e)))
        if t and t.IsValidObject and t.GetStatus() == DB.TransactionStatus.Started:
            t.RollBack()
            print("    [SAFETY] Transaction Rolled Back.")

    finally:
        # --- STEP 4: AGGRESSIVE MEMORY CLEANUP ---
        # This prevents the 'BorrowedReference' crash on the next run
        try:
            if t is not None:
                if t.IsValidObject:
                    t.Dispose()
        except Exception:
            pass

        # KILL THE PYTHON REFERENCE
        t = None
        del t

        # FORCE GARBAGE COLLECTION
        gc.collect()
        print("    [SYSTEM] Memory Released.")


if __name__ == "__main__":
    run_safe_sync()