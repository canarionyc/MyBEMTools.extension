import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

selected_ids = uidoc.Selection.GetElementIds()

if not selected_ids:
    print("Please select the walls you just dragged into the correct position!")
else:
    print("--- WALL POSITION & DRAG REPORT ---")
    for el_id in selected_ids:
        wall = doc.GetElement(el_id)
        
        if isinstance(wall, Wall):
            # THE FIX: Safely getting the name directly from the element instance
            wall_type_name = wall.Name
            loc_curve = wall.Location
            
            if isinstance(loc_curve, LocationCurve):
                # Get start and end points
                pt1 = loc_curve.Curve.GetEndPoint(0)
                pt2 = loc_curve.Curve.GetEndPoint(1)
                
                # Convert feet back to mm
                x1, y1 = pt1.X * 304.8, pt1.Y * 304.8
                x2, y2 = pt2.X * 304.8, pt2.Y * 304.8
                
                # Get the orientation (which way the "exterior" side is facing)
                facing = wall.Orientation
                
                print("Wall Type: {}".format(wall_type_name))
                print("  Start Point (mm): X = {:.1f},  Y = {:.1f}".format(x1, y1))
                print("  End Point   (mm): X = {:.1f},  Y = {:.1f}".format(x2, y2))
                print("  Facing Vector:    X = {:.1f},  Y = {:.1f}".format(facing.X, facing.Y))
                print("-" * 40)