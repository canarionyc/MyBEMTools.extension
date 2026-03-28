#! python3
import rhinoscriptsyntax as rs
import json
import os
import hashlib # NEW: Used for generating colors from text

# --- PATHS ---
PAYLOAD_PATH = r"C:\dev\MyBEMTools.extension\bem_api\output\payload.json"
RULES_PATH = r"C:\dev\MyBEMTools.extension\bem_api\data\rules.json"

def get_type_color(type_name):
    """Generates a consistent, bright RGB color based on the family or floor name."""
    if not type_name:
        return (150, 150, 150) # Fallback gray
        
    # Convert text to a unique hexadecimal number
    m = hashlib.md5(type_name.encode('utf-8'))
    h = m.hexdigest()
    
    # Use parts of the hex to create RGB values
    # We use % 156 + 100 to ensure the colors stay bright and visible!
    r = (int(h[0:2], 16) % 156) + 100
    g = (int(h[2:4], 16) % 156) + 100
    b = (int(h[4:6], 16) % 156) + 100
    
    return (r, g, b)

def generate_mockup():
    print("--- STARTING 3D BEM VALIDATION ---")
    
    if not os.path.exists(PAYLOAD_PATH) or not os.path.exists(RULES_PATH):
        print("❌ Error: Could not find payload.json or rules.json.")
        return

    # 1. Load data
    with open(PAYLOAD_PATH, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    with open(RULES_PATH, 'r', encoding='utf-8') as f:
        master_data = json.load(f)

    levels_dict = master_data.get("levels", {})
    rules = master_data.get("types", {})

    # Sort levels by elevation
    sorted_levels = sorted(
        [(name, data.get("elevation", 0.0)) for name, data in levels_dict.items()],
        key=lambda x: x[1]
    )

    # 2. Setup and CLEAR the mockup layer
    mockup_layer = "BEM-VALIDATION-MOCKUP"
    if rs.IsLayer(mockup_layer):
        existing_objs = rs.ObjectsByLayer(mockup_layer)
        if existing_objs:
            rs.DeleteObjects(existing_objs)
    else:
        # Layer itself is gray, but objects will override it
        rs.AddLayer(mockup_layer, color=(100, 100, 100))
        
    rs.CurrentLayer(mockup_layer)

    print(f"🏗️ Generating solids for {len(payload)} BEM elements...\n")
    rs.EnableRedraw(False)

    # 3. Process each payload item
    for i, item in enumerate(payload):
        debug_flag = item.get("debug_flag")
        print(f"Got {debug_flag}")
        if debug_flag == 1:
            print("here")

        coords = item.get("coordinates", [])
        category = item.get("category", "")
        payload_level = item.get("level", "")
        
        print(f"\n▶️ Processing {i+1}/{len(payload)} [{category}] on {payload_level}")
        
        if len(coords) < 2:
            continue

        rule = rules.get(category)
        if not rule:
            print(f"   ⚠️ Skipped: Category '{category}' not found in rules.json.")
            continue

        # --- A. FIND BASE ELEVATION ---
        base_z = None
        current_level_index = -1
        
        for idx, (lvl_name, z_val) in enumerate(sorted_levels):
            if lvl_name == payload_level:
                base_z = z_val
                current_level_index = idx
                break
                
        if base_z is None:
            continue

        # --- B. APPLY BASE OFFSET ---
        base_offset = float(item.get("base_offset", rule.get("base_offset", 0.0)))
        base_z += base_offset
        if base_offset != 0.0:
            print(f"   - Applied Base Offset: {base_offset}mm")

        
        pts = [rs.coerce3dpoint([pt[0], pt[1], base_z]) for pt in coords]

        # ==========================================
        # FORK IN LOGIC: FLOOR vs WALL
        # ==========================================
        if rule.get("is_floor"):
            
            # Extract the specific floor type to generate its color
            type_name = item.get("floor_type", rule.get("floor_type", "Default Floor"))
            if type_name == "Foundation Slab":
                print(type_name)

            type_color = get_type_color(type_name)
            
            print(f"   - Element Type: FLOOR | {type_name}")
            
            if rs.Distance(pts[0], pts[-1]) > 0.1:
                pts.append(pts[0])
                
            base_crv = rs.AddPolyline(pts)
            if not base_crv: continue
            thickness = float(rule.get("thickness", 200.0))    
            path_line = rs.AddLine((0, 0, base_z), (0, 0, base_z - thickness))
            extrusion = rs.ExtrudeCurve(base_crv, path_line)
            
            if extrusion:
                # CapPlanarHoles modifies the object IN PLACE (returns True/False)
                rs.CapPlanarHoles(extrusion)
                
                # Because it was capped in place, the ID 'extrusion' is still valid!
                rs.ObjectLayer(extrusion, mockup_layer)
                rs.ObjectColor(extrusion, type_color) # APPLY COLOR
            
            rs.DeleteObject(path_line)
            rs.DeleteObject(base_crv)
            
        else:
            # --- WALL LOGIC ---
            # Extract the specific wall family to generate its color
            type_name = item.get("family_name", rule.get("family_name", "Default Wall"))
            type_color = get_type_color(type_name)
            
            height = 3000.0
            top_z = None
            explicit_top = item.get("top_level") 
            
            if explicit_top:
                for lvl_name, z_val in sorted_levels:
                    if lvl_name == explicit_top:
                        top_z = z_val
                        break
                if top_z is not None:
                    height = top_z - base_z
            
            # Default Rule Logic
            if not explicit_top or top_z is None:
                top_constraint = rule.get("top_constraint", "NextLevel")
                if top_constraint == "Unconnected":
                    height = float(rule.get("unconnected_height", 3000.0))
                elif top_constraint == "NextLevel":
                    if current_level_index + 1 < len(sorted_levels):
                        height = sorted_levels[current_level_index + 1][1] - base_z
            
            # Apply Top Offset
            top_offset = item.get("top_offset", rule.get("top_offset", 0.0))
            if top_offset:
                height += float(top_offset)
                
            print("   - Element Type: WALL")
            print(f"   - Base Z: {base_z}mm | Height: {height}mm")

            if len(pts) == 2:
                base_crv = rs.AddLine(pts[0], pts[1])
            else:
                base_crv = rs.AddPolyline(pts)

            if not base_crv: continue

            path_line = rs.AddLine((0, 0, base_z), (0, 0, base_z + height))
            srf = rs.ExtrudeCurve(base_crv, path_line)
            
            rs.DeleteObject(path_line)
            rs.DeleteObject(base_crv)

            if not srf: continue

            loc_line = item.get("location_line", rule.get("location_line", "WallCenterline"))
            flip_cmd = ""
            if "Centerline" in loc_line:
                dist = thickness / 2.0
                both_sides = "_Yes"
            else:
                dist = thickness
                both_sides = "_No"
                if "Interior" in loc_line:
                    flip_cmd = "_FlipAll "
                    
            rs.UnselectAllObjects()
            rs.SelectObject(srf)
            cmd = f"_-OffsetSrf _Distance {dist} _Solid=_Yes _BothSides={both_sides} _DeleteInput=_Yes {flip_cmd}_Enter"
            rs.Command(cmd, echo=False)
            
            new_objs = rs.LastCreatedObjects()
            if new_objs:
                rs.ObjectLayer(new_objs, mockup_layer)
                
                # Apply color to all resulting solid parts of this wall
                for obj in new_objs:
                    rs.ObjectColor(obj, type_color) # APPLY COLOR

    rs.EnableRedraw(True)
    rs.ZoomExtents()
    
    # Ensure Rhino displays the object colors instead of layer colors
    rs.ViewDisplayMode(rs.CurrentView(), "Shaded")
    print("\n✅ 3D Validation Mockup Complete!")

if __name__ == "__main__":
    generate_mockup()