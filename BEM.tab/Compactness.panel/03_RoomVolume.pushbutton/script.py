# -*- coding: utf-8 -*-
import sys

# --- 1. THE NUCLEAR SILENCE OPTION ---
# We replace stdout with a Null object that does NOTHING.
# This prevents ANY library from triggering the codepage___0 crash.
class NullStream(object):
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass
    @property
    def encoding(self): return "utf-8"

sys.stdout = NullStream()
sys.stderr = NullStream()

# --- 2. SAFE IMPORTS ---
import clr
try:
    clr.AddReference("RevitAPI")
    clr.AddReference("RevitAPIUI")
except:
    pass

import Autodesk.Revit.DB as DB
import Autodesk.Revit.DB.Architecture as Arch
from pyrevit import output
from bem_utils import logger, CUFT_TO_M3 # logger must be imported AFTER stdout is silenced

def run_script():
    # Get the pyRevit output window directly (bypasses sys.stdout)
    out = output.get_output()
    
    # Access document safely
    try:
        uidoc = __revit__.ActiveUIDocument
        doc = uidoc.Document
    except Exception:
        # We use the output window directly since print/logger might still hit stdout
        out.print_md("### Error: No active Revit document found.")
        return

    # Reference types via the DB alias to avoid assembly version conflicts
    v_setting_type = DB.VolumeComputationSetting
    current_setting = doc.Settings.VolumeComputationSetting

    if current_setting == v_setting_type.NotCalculated:
        out.print_md("--- Volume calculations were **OFF**. Enabling them... ---")
        with DB.Transaction(doc, "Enable Volume Calc") as t:
            t.Start()
            doc.Settings.VolumeComputationSetting = v_setting_type.Calculated
            t.Commit()
        out.print_md("--- Volume calculations are now **ENABLED**. ---")
    
    rooms = DB.FilteredElementCollector(doc).OfClass(DB.SpatialElement).ToElements()
    
    found_rooms = 0
    for room in rooms:
        if isinstance(room, Arch.Room) and room.Area > 0:
            vol_m3 = room.Volume * CUFT_TO_M3
            # Use the output window's specific print method
            out.print_md("**Zone:** {} | **Volume:** {:.2f} m³".format(room.Name, vol_m3))
            found_rooms += 1
            
    if found_rooms == 0:
        out.print_md("_No valid rooms with area found in this model._")
    else:
        out.print_md("--- Processed **{}** rooms successfully. ---".format(found_rooms))

if __name__ == "__main__":
    run_script()
