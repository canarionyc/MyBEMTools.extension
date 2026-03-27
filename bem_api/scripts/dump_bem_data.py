#! python 3
import rhinoscriptsyntax as rs
import json
import os

def dump_bem_data():
    # Pointing to your exact API payload folder
    json_file = r"C:\dev\MyBEMTools.extension\bem_api\payloads\wall_maker.json"
    
    payload = {
        "exterior_walls": [],
        "interior_walls": [],
        "doors": []
    }

    print("--- EXTRACTING RHINO GEOMETRY ---")

    # 1. Extract Exterior Walls (Handles both Lines and Polylines)
    ext_objs = rs.ObjectsByLayer("BEM-WALLS-EXTERIOR")
    if ext_objs:
        for obj in ext_objs:
            if rs.IsPolyline(obj):
                vertices = rs.PolylineVertices(obj)
                for i in range(len(vertices)-1):
                    payload["exterior_walls"].append({
                        "start": [round(vertices[i].X, 2), round(vertices[i].Y, 2)],
                        "end": [round(vertices[i+1].X, 2), round(vertices[i+1].Y, 2)]
                    })
            elif rs.IsLine(obj):
                start = rs.CurveStartPoint(obj)
                end = rs.CurveEndPoint(obj)
                payload["exterior_walls"].append({
                    "start": [round(start.X, 2), round(start.Y, 2)],
                    "end": [round(end.X, 2), round(end.Y, 2)]
                })

    # 2. Extract Interior Walls
    int_objs = rs.ObjectsByLayer("BEM-WALLS-INTERIOR")
    if int_objs:
        for obj in int_objs:
            if rs.IsLine(obj):
                start = rs.CurveStartPoint(obj)
                end = rs.CurveEndPoint(obj)
                payload["interior_walls"].append({
                    "start": [round(start.X, 2), round(start.Y, 2)],
                    "end": [round(end.X, 2), round(end.Y, 2)]
                })

    # 3. Extract Doors (Blocks)
    door_objs = rs.ObjectsByLayer("BEM-DOORS")
    if door_objs:
        for obj in door_objs:
            if rs.IsBlockInstance(obj):
                name = rs.BlockInstanceName(obj)
                pt = rs.BlockInstanceInsertPoint(obj)
                payload["doors"].append({
                    "type": name,
                    "location": [round(pt.X, 2), round(pt.Y, 2)],
                    "rotation": 0.0 # Simplifying rotation for this quick dump
                })

    # 4. Save to JSON
    with open(json_file, 'w') as f:
        json.dump(payload, f, indent=2)
        
    print("SUCCESS! Dumped BEM Data to: {}".format(json_file))
    print("Found: {} Exterior Segments, {} Interior Walls, {} Doors.".format(
        len(payload["exterior_walls"]), len(payload["interior_walls"]), len(payload["doors"])
    ))

if __name__ == "__main__":
    dump_bem_data()