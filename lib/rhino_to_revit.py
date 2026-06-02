#! python 3
from pprint import pprint
#%% SETUP AND IMPORTS
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RhinoCommon")

import Rhino.Geometry as rg
from Autodesk.Revit.DB import Document, Floor, Level, FloorType, FilteredElementCollector, Transaction, CurveLoop
from System.Collections.Generic import List
import RhinoInside.Revit as rir
from RhinoInside.Revit.Convert.Geometry import GeometryEncoder
from pprint import pprint

doc = rir.Revit.ActiveDBDocument





# %% TRANSLATE GEOMETRY TO ORIGIN BEFORE REVIT CREATION
import Rhino.Geometry as rg


def translate_to_local_origin(geometry: rg.GeometryBase) -> rg.GeometryBase:
    """
    Applies a translation vector to move geometry from UTM28N
    to a local 0,0,0 origin purely in memory.
    """
    # Define the inverse of your site's UTM centroid.
    # Replace these with your actual UTM Easting and Northing reference points.
    easting_offset = -370000.0
    northing_offset = -3150000.0
    elevation_offset = 0.0  # Leave Z alone if your levels are already correct

    # Create the translation vector and matrix
    offset_vector = rg.Vector3d(easting_offset, northing_offset, elevation_offset)
    translation = rg.Transform.Translation(offset_vector)

    # Duplicate the geometry so we don't accidentally move the live Rhino object
    local_geometry = geometry.Duplicate()

    # Apply the transform
    local_geometry.Transform(translation)

    return local_geometry


#%% DEMONSTRATION
if __name__ == "__main__":
    # --- MOCKING THE INPUT ---

    live_canvas_data = dump_rhino_canvas_by_layer()
    pprint(live_canvas_data)

    # In your live script, 'my_extrusion' comes directly from your layer dump dictionary:
    my_extrusion = live_canvas_data['Storey_-4.200::IfcSlab_Floor'][0]['geometry']

    centered_extrusion = translate_to_local_origin(my_extrusion)
    # Here we create a mock 3D extrusion (a 5x5m slab, 0.3m thick) to demonstrate


    # rect = rg.Rectangle3d(rg.Plane.WorldXY, 5.0, 5.0)
    # mock_base_curve = rect.ToNurbsCurve()
    # my_extrusion = rg.Extrusion.Create(mock_base_curve, 0.3, True)
    
    # --- REVIT TARGETS ---
    target_level = FilteredElementCollector(doc).OfClass(Level).FirstElement()
    target_floor_type = FilteredElementCollector(doc).OfClass(FloorType).WhereElementIsElementType().FirstElement()
    
    pprint("--- Starting Direct Slab Generation ---")
    my_new_slab = create_revit_floor_from_extrusion(
        extrusion=my_extrusion,
        level=target_level,
        floor_type=target_floor_type
    )
    pprint("--- Generation Complete ---")