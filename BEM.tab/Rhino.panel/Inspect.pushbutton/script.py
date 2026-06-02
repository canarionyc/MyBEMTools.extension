#! python3
# -*- coding: utf-8 -*-
from pprint import pprint

# %% PYREVIT SCRIPT: SILENT 3DM PROCESSING
import clr
import sys

# 1. Verify Rhino.Inside is loaded in the current Revit session
try:
    clr.AddReference("RhinoInside.Revit")
    import RhinoInside.Revit as rir
except IOError:
    print("Error: Rhino.Inside.Revit is not installed or loaded.")
    sys.exit()

# 2. Boot the Rhino engine in the background (Corrected API Call)
try:
    rir.Revit.Startup()
except Exception as e:
    # If Rhino is already running (e.g., the user clicked "Start" in the Ribbon),
    # we catch the exception and proceed seamlessly.
    pass

# 3. Now the RhinoCommon assembly resolver is active, and it is safe to load
try:
    clr.AddReference("RhinoCommon")
    import Rhino.Geometry as rg
    import Rhino.FileIO as fileio
except IOError:
    print("Error: Could not load RhinoCommon. Ensure Rhino 8 is installed.")
    sys.exit()


def process_3dm_silently(filepath: str):
    """
    Opens a 3dm file in memory, extracts geometry,
    and passes it to Revit, all without opening Rhino.
    """
    # Read the file purely into memory
    file_3dm = fileio.File3dm.Read(filepath)
    if not file_3dm:
        print(f"Failed to read: {filepath}")
        return

    print(f"Successfully loaded 3dm: {filepath}")

    # Iterate through the objects in the file
    for obj in file_3dm.Objects:
        geom = obj.Geometry
        print(f"Processing object: {obj.Id} of type {type(geom)}")

        # Because the Rhino core is running invisibly via RIR,
        # complex geometric math is now available.
        if isinstance(geom, rg.Extrusion):
            # Your Brep/Normal extraction logic from earlier will work perfectly here
            # bottom_profile = extract_bottom_profile_from_solid(geom)
            # create_revit_floor_from_extrusion(...)
            pass

    # file_3dm.Dispose() is handled automatically in python,
    # but good practice for memory management in large files.
    file_3dm.Dispose()

#%% DEMONSTRATION
if __name__ == "__main__":
    filepath = r"C:\dev\PteZurita\Rhino\Layout_Stacked_3D_260521_260522_031847_Grouped_20260522_041010.3dm"
    process_3dm_silently(filepath)