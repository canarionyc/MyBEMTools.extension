#! python3
import rhinoscriptsyntax as rs
import json
import os
import hashlib

# --- PATHS ---
PAYLOAD_PATH = r"C:\dev\MyBEMTools.extension\bem_api\output\payload.json"
RULES_PATH = r"C:\dev\MyBEMTools.extension\bem_api\data\rules.json"

def get_type_color(type_name):
    if not type_name: return (150, 150, 150)
    m = hashlib.md5(type_name.encode('utf-8'))
    h = m.hexdigest()
    r = (int(h[0:2], 16) % 156) + 100
    g = (int(h[2:4], 16) % 156) + 100
    b = (int(h[4:6], 16) % 156) + 100
    return (r, g, b)

def apply_attributes_to_solid(solid_id, item_dict):
    """Copies all text/number attributes from the JSON payload to the 3D solid."""
    for key, value in item_dict.items():
        # Skip complex data structures like coordinates lists
        if isinstance(value, (str, int, float, bool)):
            rs.SetUserText(solid_id, key, str(value))

def generate_mockup():
    print("--- STARTING 3D BEM VALIDATION ---")
    
    if not os.path.exists(PAYLOAD_PATH) or not os.path.exists(RULES_PATH):
        print("❌ Error: Could not find payload.json or rules.json.")
        return

    with open(PAYLOAD_PATH, 'r', encoding='utf-8') as f: payload_dict = json.load(f)
    with open(RULES_PATH, 'r', encoding='utf-8') as f: master_data = json.load(f)

    # NEW FIX: Flatten the level-keyed dictionary into a single list of objects
    payload = []
    for level_items in payload_dict.values():
        payload.extend(level_items)

    levels_dict = master_data.get("levels", {})
    rules = master_data.get("types", {})
    sorted_levels = sorted([(name, data.get("elevation", 0.0)) for name, data in levels_dict.items()], key=lambda x: x[1])

    # POINT 4 FIX: Capture the current layer before we do anything
    original_layer = rs.CurrentLayer()

    mockup_layer = "BEM-VALIDATION-MOCKUP"
    if rs.IsLayer(mockup_layer):
        existing_objs = rs.ObjectsByLayer(mockup_layer)
        if existing_objs: rs.DeleteObjects(existing_objs)
    else:
        rs.AddLayer(mockup_layer, color=(100, 100, 100))
        
    rs.CurrentLayer(mockup_layer)
    rs.EnableRedraw(False)

    for i, item in enumerate(payload):
        coords = item.get("coordinates", [])
        category = item.get("category", "")
        payload_level = item.get("level", "")
        
        if len(coords) < 2: continue
        rule = rules.get(category)
        if not rule: continue

        base_z = None
        current_level_index = -1
        for idx, (lvl_name, z_val) in enumerate(sorted_levels):
            if lvl_name == payload_level:
                base_z = z_val
                current_level_index = idx
                break
                
        if base_z is None: continue

        base_offset = float(item.get("base_offset", rule.get("base_offset", 0.0)))
        base_z += base_offset
        thickness = float(rule.get("thickness", 200.0))
        pts = [rs.coerce3dpoint([pt[0], pt[1], base_z]) for pt in coords]

        if rule.get("is_floor"):
            type_name = item.get("floor_type", rule.get("floor_type", "Default Floor"))
            if rs.Distance(pts[0], pts[-1]) > 0.1: pts.append(pts[0])
            base_crv = rs.AddPolyline(pts)
            if not base_crv: continue
                
            path_line = rs.AddLine((0, 0, base_z), (0, 0, base_z - thickness))
            extrusion = rs.ExtrudeCurve(base_crv, path_line)
            
            if extrusion:
                rs.CapPlanarHoles(extrusion)
                rs.ObjectLayer(extrusion, mockup_layer)
                rs.ObjectColor(extrusion, get_type_color(type_name))
                # POINT 3 FIX: Apply attributes
                apply_attributes_to_solid(extrusion, item)
            
            rs.DeleteObject(path_line)
            rs.DeleteObject(base_crv)
            
        else:
            type_name = item.get("family_name", rule.get("family_name", "Default Wall"))
            height = 3000.0
            top_z = None
            explicit_top = item.get("top_level") 
            
            if explicit_top:
                for lvl_name, z_val in sorted_levels:
                    if lvl_name == explicit_top: top_z = z_val; break
                if top_z is not None: height = top_z - base_z
            
            if not explicit_top or top_z is None:
                top_constraint = rule.get("top_constraint", "NextLevel")
                if top_constraint == "Unconnected":
                    height = float(rule.get("unconnected_height", 3000.0))
                elif top_constraint == "NextLevel" and current_level_index + 1 < len(sorted_levels):
                    height = sorted_levels[current_level_index + 1][1] - base_z
            
            top_offset = float(item.get("top_offset", rule.get("top_offset", 0.0)))
            height += top_offset

            base_crv = rs.AddLine(pts[0], pts[1]) if len(pts) == 2 else rs.AddPolyline(pts)
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
                if "Interior" in loc_line: flip_cmd = "_FlipAll "
                    
            rs.UnselectAllObjects()
            rs.SelectObject(srf)
            cmd = f"_-OffsetSrf _Distance {dist} _Solid=_Yes _BothSides={both_sides} _DeleteInput=_Yes {flip_cmd}_Enter"
            rs.Command(cmd, echo=False)
            
            new_objs = rs.LastCreatedObjects()
            if new_objs:
                rs.ObjectLayer(new_objs, mockup_layer)
                for obj in new_objs:
                    rs.ObjectColor(obj, get_type_color(type_name))
                    # POINT 3 FIX: Apply attributes
                    apply_attributes_to_solid(obj, item)

    # POINT 4 FIX: Clean up selection and restore original layer
    rs.UnselectAllObjects()
    rs.CurrentLayer(original_layer)
    rs.EnableRedraw(True)
    rs.ViewDisplayMode(rs.CurrentView(), "Shaded")
    print("\n✅ 3D Validation Mockup Complete!")

if __name__ == "__main__":
    generate_mockup()