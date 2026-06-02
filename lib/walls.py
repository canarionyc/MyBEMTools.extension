#! python 3
from pprint import pprint
#%% SETUP AND IMPORTS
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RhinoCommon")

import Rhino.Geometry as rg
from Autodesk.Revit.DB import Document, Wall, Level, WallType, FilteredElementCollector, Transaction
import RhinoInside.Revit as rir
from RhinoInside.Revit.Convert.Geometry import GeometryEncoder

# Reference the active Revit document
doc = rir.Revit.ActiveDBDocument

#%% WALL GENERATION FUNCTION
def create_revit_walls_from_rhino(
    rhino_curves: list[rg.Curve], 
    level: Level, 
    wall_type: WallType, 
    height_meters: float
) -> list[Wall]:
    """
    Translates a list of Rhino curves into native Revit walls using Rhino.Inside.Revit.
    """
    created_walls: list[Wall] = []
    
    # Revit API internal units are decimal feet
    height_feet: float = height_meters / 0.3048 
    
    t = Transaction(doc, "Generate Walls from Rhino")
    t.Start()
    
    try:
        for crv in rhino_curves:
            # 1. Convert Rhino Curve to Revit Curve safely in Rhino 8
            revit_curve = GeometryEncoder.ToCurve(crv)
            
            # 2. Generate the native Revit element
            # Signature: Wall.Create(Document, Curve, ElementId wallTypeId, ElementId levelId, double height, double offset, bool flip, bool structural)
            new_wall = Wall.Create(
                doc, 
                revit_curve, 
                wall_type.Id, 
                level.Id, 
                height_feet, 
                0.0, 
                False, 
                False
            )
            created_walls.append(new_wall)
            
        t.Commit()
        pprint(f"Successfully created {len(created_walls)} walls.")
        
    except Exception as e:
        t.RollBack()
        pprint(f"Transaction failed: {e}")
        
    return created_walls

#%% DEMONSTRATION
if __name__ == "__main__":
    # Create mock curves to test the dispatcher logic
    line1 = rg.LineCurve(rg.Point3d(0, 0, 0), rg.Point3d(4, 0, 0))
    line2 = rg.LineCurve(rg.Point3d(4, 0, 0), rg.Point3d(4, 3, 0))
    mock_rhino_curves: list[rg.Curve] = [line1, line2]
    
    try:
        # Dynamically fetch the first available Level and WallType in the active document
        target_level = FilteredElementCollector(doc).OfClass(Level).FirstElement()
        target_wall_type = FilteredElementCollector(doc).OfClass(WallType).WhereElementIsElementType().FirstElement()
        
        if target_level and target_wall_type:
            pprint("--- Testing Direct Wall Generation ---")
            pprint(f"Target Level: {target_level.Name}")
            pprint(f"Target WallType: {target_wall_type.Name}")
            
            # Execute the function
            my_new_walls = create_revit_walls_from_rhino(
                rhino_curves=mock_rhino_curves,
                level=target_level,
                wall_type=target_wall_type,
                height_meters=3.2  
            )
            pprint("--- Test Complete ---")
        else:
            pprint("Error: Could not find a valid Level or WallType in the document.")
            
    except Exception as doc_error:
        pprint(f"Error accessing Revit data: {doc_error}")