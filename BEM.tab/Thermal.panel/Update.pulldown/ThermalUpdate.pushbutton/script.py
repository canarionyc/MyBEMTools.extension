#! python3
# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
import importlib
import gc
from pyrevit import DB, script

# Force reload
import bem_env

importlib.reload(bem_env)
from bem_env import update_material_thermal_data, db_path

output = script.get_output()
output.print_md("# BEM SYNC: Scope-Isolated (Final Fix)")


def _core_logic(doc):
    """
    This inner function handles the logic.
    When this function returns, the variable 't' (Transaction)
    goes out of scope naturally, making it easier to collect.
    """
    t = None
    try:
        # --- DATABASE ---
        if not os.path.exists(db_path):
            print("    [ERROR] Database not found.")
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

        # --- TRANSACTION ---
        print(">>> Starting Transaction (Inner Scope)...")
        t = DB.Transaction(doc, "BEM: Sync SOL CAM SANIT")
        t.Start()

        # Find Type
        target_name = "SOL CAM SANIT"
        target_type = None

        col = DB.FilteredElementCollector(doc).OfClass(DB.FloorType)
        for ft in col:
            p = ft.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
            if p and p.AsString() == target_name:
                target_type = ft
                break
        del col  # Immediate cleanup

        if not target_type:
            print("    [ERROR] FloorType '{}' not found.".format(target_name))
            t.RollBack()
            return

        # Update Structure
        struct = target_type.GetCompoundStructure()
        for i, row in enumerate(db_layers):
            if i < struct.LayerCount:
                # bem_env Logic
                mat_id = update_material_thermal_data(doc, row)

                # Thickness
                thickness_ft = float(row['thickness']) / 0.3048

                struct.SetMaterialId(i, mat_id)
                struct.SetLayerWidth(i, thickness_ft)
                print("    > Layer {}: Updated".format(i))

        target_type.SetCompoundStructure(struct)

        t.Commit()
        output.print_md("### SUCCESS: Transaction Committed")

    except Exception as e:
        print("\n[CRITICAL FAILURE]: {}".format(str(e)))
        if t and t.IsValidObject and t.GetStatus() == DB.TransactionStatus.Started:
            t.RollBack()
            print("    [SAFETY] Transaction Rolled Back.")
        raise e  # Re-raise to trigger outer cleanup

    finally:
        # Dispose inside the inner scope
        if t and t.IsValidObject:
            t.Dispose()


def run_safe_sync():
    """
    The Outer Shell. Its only job is to run the logic
    and then SCRUB memory.
    """
    # 1. Get Doc
    uidoc = __revit__.ActiveUIDocument
    if not uidoc: return
    doc = uidoc.Document

    print(">>> STEP 1: Initializing...")

    try:
        _core_logic(doc)
    except Exception:
        pass  # Error already printed in inner scope

    finally:
        # --- THE NUCLEAR CLEANUP ---
        print(">>> STEP 2: System Cleanup...")

        # 1. Clear the Python System Error Cache
        # This releases the Stack Trace which holds the Transaction variable
        sys.last_type = None
        sys.last_value = None
        sys.last_traceback = None

        # 2. Force Garbage Collection (Twice is safer for .NET bridges)
        gc.collect()
        gc.collect()

        print("    [SYSTEM] Memory Scrubbed. Safe to re-run.")


if __name__ == "__main__":
    run_safe_sync()