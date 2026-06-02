#! python3
from pprint import pprint
# -*- coding: utf-8 -*-
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

# #%% SETUP AND IMPORTS
# import clr
# clr.AddReference("RevitAPI")
# import Rhino.Geometry as rg
# from Autodesk.Revit.DB import Document, Transaction
# from pprint import pprint

# Assuming the creation functions from our previous cells are loaded:
from rhino_to_revit import translate_to_local_origin
from slabs import create_revit_floor_from_extrusion
from walls import create_revit_walls_from_rhino

#%% DISPATCHER LOGIC
def process_rhino_objects_to_revit(rhino_objects_data: list, target_level, wall_type, floor_type):
    """
    Loops through a list of Rhino objects, applies a universal coordinate 
    translation, and routes them to the correct Revit creation function 
    based on naming conventions.
    """
    results = {"walls": 0, "floors": 0, "failed or skipped": 0}
    
    for obj in rhino_objects_data:
        original_geom = obj.get("geometry")
        if not original_geom:
            continue
            
        # 1. UNIVERSAL TRANSFORMATION: 
        # Shift the geometry from UTM to local origin regardless of its type
        local_geom = translate_to_local_origin(original_geom)
        
        # 2. ROUTING LOGIC:
        # Use the layer name or object name to determine the native category
        classification = obj.get("layer_name", "").lower()
        
        if "wall" in classification:
            # We need a base curve for walls
            if isinstance(local_geom, rg.Extrusion) or isinstance(local_geom, rg.Brep):
                # (You would use a curve extraction function here)
                pass 
            elif isinstance(local_geom, rg.Curve):
                create_revit_walls_from_rhino([local_geom], target_level, wall_type, 3.2)
                results["walls"] += 1
                
        elif "slab" in classification or "floor" in classification:
            # We know from earlier this is an Extrusion
            if isinstance(local_geom, rg.Extrusion):
                create_revit_floor_from_extrusion(local_geom, target_level, floor_type)
                results["floors"] += 1
            else:
                pprint(f"Skipped slab: Geometry is not an Extrusion ({type(local_geom)})")
                results["failed or skipped"] += 1
                
        else:
            pprint(f"Unrecognized classification for routing: {classification}")
            results["failed or skipped"] += 1

    return results

#%% DEMONSTRATION
if __name__ == "__main__":
    # Mocking the data structure you provided earlier
    mock_layer_data = [
        {
            'layer_name': 'Storey_-4.200::IfcSlab_Floor',
            'geometry': rg.Extrusion.Create(rg.Rectangle3d(rg.Plane.WorldXY, 5.0, 5.0).ToNurbsCurve(), 0.3, True),
            'guid': '80f44171-4b55-4abf-9261-513cf162ff78',
        },
        {
            'layer_name': 'Storey_-4.200::IfcWallStandardCase',
            'geometry': rg.LineCurve(rg.Point3d(0, 0, 0), rg.Point3d(10, 0, 0)),
            'guid': 'a92596d5-d4c5-4e61-8024-c488b2ef6966',
        }
    ]
    
    # In reality, fetch these from your Revit doc
    mock_level = None 
    mock_wall_type = None
    mock_floor_type = None
    
    pprint("--- Starting Batch Dispatch ---")
    # Uncomment in live environment:
    # batch_results = process_rhino_objects_to_revit(mock_layer_data, mock_level, mock_wall_type, mock_floor_type)
    # pprint(batch_results)
    pprint("--- Batch Complete ---")