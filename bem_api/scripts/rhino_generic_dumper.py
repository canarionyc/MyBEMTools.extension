import rhinoscriptsyntax as rs
import json
import os

OUTPUT_DIR = r"C:\dev\MyBEMTools.extension\bem_api\output"

def is_orthogonal(p1, p2, tol=0.01):
    """Returns True if the line segment is strictly vertical or horizontal"""
    dx = abs(p1.X - p2.X)
    dy = abs(p1.Y - p2.Y)
    return dx < tol or dy < tol

def check_polyline_ortho(pts, tol=0.01):
    """Checks all segments of a polyline. Returns True if all are orthogonal."""
    for i in range(len(pts) - 1):
        if not is_orthogonal(pts[i], pts[i+1], tol):
            return False
    return True

def smart_generic_dumper():
    json_file = os.path.join(OUTPUT_DIR, "generic_dump.json")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # NEW STRUCTURE: A dictionary where Keys are Layers
    payload = {}

    print("--- STARTING SMART RHINO DUMP & QC ---")

    all_objs = rs.AllObjects()
    if not all_objs:
        print("ERROR: No objects found in the file.")
        return

    stats = {"lines": 0, "polylines": 0, "blocks": 0, "other": 0, "qc_errors": 0}

    for obj in all_objs:
        layer = rs.ObjectLayer(obj)
        
        # Initialize the layer in our dictionary if it doesn't exist yet
        if layer not in payload:
            payload[layer] = {
                "lines": [],
                "polylines": [],
                "blocks": [],
                "other_objects": []
            }

        # Safely get attributes
        attributes = {}
        user_keys = rs.GetUserText(obj)
        if user_keys:
            for key in user_keys:
                attributes[key] = rs.GetUserText(obj, key)

        obj_type = rs.ObjectType(obj)

        # TYPE 4 = CURVE
        if obj_type == 4:
            if rs.IsLine(obj):
                start = rs.CurveStartPoint(obj)
                end = rs.CurveEndPoint(obj)
                
                line_data = {
                    "id": str(obj),
                    "tags": attributes,
                    "start": [round(start.X, 2), round(start.Y, 2)],
                    "end": [round(end.X, 2), round(end.Y, 2)]
                }
                
                # QC CHECK
                if not is_orthogonal(start, end):
                    line_data["qc_warning"] = "NON-ORTHOGONAL"
                    stats["qc_errors"] += 1
                    
                payload[layer]["lines"].append(line_data)
                stats["lines"] += 1

            elif rs.IsPolyline(obj):
                pts = rs.PolylineVertices(obj)
                if pts:
                    poly_data = {
                        "id": str(obj),
                        "tags": attributes,
                        "is_closed": rs.IsCurveClosed(obj),
                        "vertices": [[round(pt.X, 2), round(pt.Y, 2)] for pt in pts]
                    }
                    
                    # QC CHECK
                    if not check_polyline_ortho(pts):
                        poly_data["qc_warning"] = "NON-ORTHOGONAL SEGMENT DETECTED"
                        stats["qc_errors"] += 1
                        
                    payload[layer]["polylines"].append(poly_data)
                    stats["polylines"] += 1
            else:
                payload[layer]["other_objects"].append({"id": str(obj), "type": "Other Curve"})
                stats["other"] += 1

        # TYPE 4096 = BLOCK INSTANCE
        elif obj_type == 4096:
            name = rs.BlockInstanceName(obj)
            pt = rs.BlockInstanceInsertPoint(obj)
            payload[layer]["blocks"].append({
                "id": str(obj),
                "type": name,
                "tags": attributes,
                "location": [round(pt.X, 2), round(pt.Y, 2)]
            })
            stats["blocks"] += 1

        # EVERYTHING ELSE
        else:
            type_name = "Unknown"
            if obj_type == 1: type_name = "Point"
            elif obj_type == 8: type_name = "Surface/Picture"
            elif obj_type == 16: type_name = "Polysurface"
            elif obj_type == 32: type_name = "Mesh"
            elif obj_type == 512: type_name = "Annotation/Text"
            elif obj_type == 65536: type_name = "Hatch"
            
            payload[layer]["other_objects"].append({
                "id": str(obj),
                "type_name": type_name,
                "tags": attributes
            })
            stats["other"] += 1

    # Save to JSON
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
            
        print("✅ SUCCESS! Dumped geometry to: {}".format(json_file))
        print("📊 STATS: {} Lines, {} Polylines, {} Blocks, {} Other".format(
            stats["lines"], stats["polylines"], stats["blocks"], stats["other"]
        ))
        if stats["qc_errors"] > 0:
            print("⚠️ WARNING: Found {} non-orthogonal objects! Check the JSON for 'qc_warning'.".format(stats["qc_errors"]))
        else:
            print("🌟 QC PASSED: All lines and polylines are perfectly orthogonal.")
            
    except Exception as e:
        print("❌ ERROR writing file: {}".format(e))

if __name__ == "__main__":
    smart_generic_dumper()