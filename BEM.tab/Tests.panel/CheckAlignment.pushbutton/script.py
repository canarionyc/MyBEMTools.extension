import json
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document
MM_TO_FT = 1 / 304.8  

def get_default_level(doc):
    collector = FilteredElementCollector(doc).OfClass(Level)
    return collector.FirstElement()

def get_wall_type(doc, thickness_tag, is_exterior):
    target_name = "Por defecto - 20 cm" if thickness_tag == "200" else "Tabique - 10 cm"
            
    collector = FilteredElementCollector(doc).OfClass(WallType)
    for w_type in collector:
        # THE FIX: Safely getting the name to prevent the ERROR: Name
        type_name_param = w_type.LookupParameter("Type Name")
        name_str = type_name_param.AsString() if type_name_param else ""
        
        # Fallback just in case
        if not name_str:
            try:
                name_str = w_type.Name
            except:
                pass
                
        if target_name in name_str:
            return w_type
            
    for w_type in collector:
        if w_type.Kind == WallKind.Basic:
            return w_type
    return None

def generate_perfect_flush():
    json_path = r"C:\dev\computer-vision-testing\Rhino8\bem_dump.json"
    
    with open(json_path, 'r') as f:
        payload = json.load(f)

    level = get_default_level(doc)
    default_height = 3000 * MM_TO_FT 
    
    t = Transaction(doc, "Generate Offset Centerlines")
    t.Start()

    try:
        for line_data in payload.get("lines", []):
            layer = line_data.get("layer", "")
            if not layer.upper().startswith("BEM-"):
                continue
                
            is_ext = "EXT" in layer.upper()
            thickness_mm = 200.0 if is_ext else 100.0
            wall_type = get_wall_type(doc, str(int(thickness_mm)), is_ext)

            # Get original Rhino coordinates
            x1, y1 = line_data["start"][0], line_data["start"][1]
            x2, y2 = line_data["end"][0], line_data["end"][1]
            
            # --- THE MATHEMATICAL ALIGN MACRO ---
            # To make the wall grow entirely to the "Left" (Up), 
            # we push the centerline UP by exactly half its thickness.
            offset_y = thickness_mm / 2.0
            
            # Apply the offset to Y, and convert to feet for Revit
            start_pt = XYZ(x1 * MM_TO_FT, (y1 + offset_y) * MM_TO_FT, 0)
            end_pt = XYZ(x2 * MM_TO_FT, (y2 + offset_y) * MM_TO_FT, 0)
            
            geom_line = Line.CreateBound(start_pt, end_pt)
            
            # Create the wall perfectly on its new calculated Centerline (0)
            new_wall = Wall.Create(doc, geom_line, wall_type.Id, level.Id, default_height, 0, False, False)
            
            loc_line_param = new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM)
            loc_line_param.Set(0) # Strictly centerline!

        t.Commit()
        print("SUCCESS: Centerlines offset manually. Walls should be perfectly flush at Y=0!")

    except Exception as e:
        t.RollBack()
        print("ERROR: " + str(e))

if __name__ == "__main__":
    generate_perfect_flush()