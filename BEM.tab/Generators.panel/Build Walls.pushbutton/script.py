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
    # Translate your Rhino thickness to Revit's specific Spanish names
    target_name = ""
    
    if thickness_tag == "200":
        target_name = "Por defecto - 20 cm"
    elif thickness_tag == "100":
        if is_exterior:
            target_name = "Por defecto - 10 cm"
        else:
            target_name = "Tabique - 10 cm"
            
    collector = FilteredElementCollector(doc).OfClass(WallType)
    for w_type in collector:
        type_name = w_type.LookupParameter("Type Name")
        name_str = type_name.AsString() if type_name else w_type.Name
        
        if target_name and target_name in name_str:
            return w_type
            
    # Fallback to any basic wall if names don't match
    for w_type in collector:
        if w_type.Kind == WallKind.Basic:
            return w_type
    return None

def mm_to_xyz(pt_array):
    return XYZ(pt_array[0] * MM_TO_FT, pt_array[1] * MM_TO_FT, 0)

def generate_bem_walls():
    # Update this to point to your new generic_dump.json!
    json_path = r"C:\dev\computer-vision-testing\Rhino8\bem_dump.json"
    
    with open(json_path, 'r') as f:
        payload = json.load(f)

    level = get_default_level(doc)
    default_height = 3000 * MM_TO_FT 
    
    t = Transaction(doc, "Generate BEM Walls (Grow Left Rule)")
    t.Start()

    try:
        # --- PROCESS INTERIOR PARTITIONS (Single Lines) ---
        for line_data in payload.get("lines", []):
            layer = line_data.get("layer", "")
            
            # THE NEW SAFETY FILTER: Ignore non-BEM layers
            if not layer.upper().startswith("BEM-"):
                continue
                
            tags = line_data.get("tags", {})
            
            # Read thickness (fallback to 100)
            is_ext = "EXT" in layer.upper()
            thickness = tags.get("BEM_Thickness", "100") 
            wall_type = get_wall_type(doc, thickness, is_ext)

            start_pt = mm_to_xyz(line_data["start"])
            end_pt = mm_to_xyz(line_data["end"])
            
            if start_pt.DistanceTo(end_pt) > 0.01:
                geom_line = Line.CreateBound(start_pt, end_pt)
                new_wall = Wall.Create(doc, geom_line, wall_type.Id, level.Id, default_height, 0, False, False)
                
                loc_line_param = new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM)
                loc_line_param.Set(3)

        # --- PROCESS ENVELOPE (Polylines) ---
        for poly_data in payload.get("polylines", []):
            layer = poly_data.get("layer", "")
            
            # THE NEW SAFETY FILTER: Ignore non-BEM layers
            if not layer.upper().startswith("BEM-"):
                continue
                
            tags = poly_data.get("tags", {})
            
            is_ext = "EXT" in layer.upper()
            thickness = tags.get("BEM_Thickness", "200")
            wall_type = get_wall_type(doc, thickness, is_ext)
            
            vertices = poly_data.get("vertices", [])

            for i in range(len(vertices) - 1):
                start_pt = mm_to_xyz(vertices[i])
                end_pt = mm_to_xyz(vertices[i+1])
                
                if start_pt.DistanceTo(end_pt) > 0.01:
                    geom_line = Line.CreateBound(start_pt, end_pt)
                    new_wall = Wall.Create(doc, geom_line, wall_type.Id, level.Id, default_height, 0, False, False)
                    
                    loc_line_param = new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM)
                    loc_line_param.Set(3)

        t.Commit()
        print("SUCCESS: Generated walls using the 'Grow to the Left' universal rule.")

    except Exception as e:
        t.RollBack()
        print("ERROR: Failed to generate walls. " + str(e))

if __name__ == "__main__":
    generate_bem_walls()