# -*- coding: utf-8 -*-
import json
import math


def decode_wall_name(name):
    """
    Decodes the BEM wall name based on the naming convention provided.
    """
    parts = name.split('_')
    floor = parts[0] if len(parts) > 0 else "Unknown"
    space = parts[1] if len(parts) > 1 else "Unknown"
    code = parts[2][:3] if len(parts) > 2 else ""  # Get first 3 letters (PCT, FTE, PE, CUB)

    mapping = {
        "PCT": "Buried Wall (Contacto Terreno)",
        "FTE": "Floor Slab (Forjado Terreno)",
        "PE": "Exterior Wall",
        "C": "Roof (Cubierta)",
        "CUB": "Roof (Cubierta)"
    }

    type_desc = mapping.get(code, "Interior/Other Surface")
    return "{} | {} | {}".format(floor, space, type_desc)


def get_global_vertices(wall_json):
    """
    Calculates 3D coordinates using the Screw Rule (CCW = Exterior Normal).
    """
    geom = wall_json['geometry']
    pos = geom['position']

    # HULC/EnvolventeCTE: 0=S, 90=E, 180=N, 270=W
    az_rad = math.radians(geom['azimuth'])
    tilt_rad = math.radians(geom['tilt'])

    # 1. Basis Vectors (Vx, Vy) derived so that Vx * Vy = Exterior Normal
    # Vx is the horizontal vector of the wall plane
    vx = [math.cos(az_rad), math.sin(az_rad), 0]

    # Vy is the vertical/slope vector of the wall plane
    vy = [
        -math.cos(tilt_rad) * math.sin(az_rad),
        math.cos(tilt_rad) * math.cos(az_rad),
        math.sin(tilt_rad)
    ]

    global_pts = []
    for px, py in geom['polygon']:
        # Transformation: Position + (LocalX * Vx) + (LocalY * Vy)
        gx = pos[0] + (px * vx[0]) + (py * vy[0])
        gy = pos[1] + (px * vx[1]) + (py * vy[1])
        gz = pos[2] + (px * vx[2]) + (py * vy[2])
        global_pts.append((round(gx, 3), round(gy, 3), round(gz, 3)))

    return global_pts


def run_diagnostic(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)

    print("{:<20} | {:<40} | {:<15}".format("WALL ID", "BEM CLASSIFICATION", "STATUS"))
    print("-" * 80)

    for wall in data['walls']:
        name = wall.get('name', 'Unnamed')
        classification = decode_wall_name(name)

        # Calculate the 3D geometry
        try:
            vertices = get_global_vertices(wall)

            print("\n[{}] {}".format(name, classification))
            print("  - Position: {}".format(wall['geometry']['position']))
            print(
                "  - Orientation: Azimuth {}°, Tilt {}°".format(wall['geometry']['azimuth'], wall['geometry']['tilt']))

            # Print the 3D loop
            for i, v in enumerate(vertices):
                print("    Point {}: (X: {:>6}, Y: {:>6}, Z: {:>6})".format(i, v[0], v[1], v[2]))

            # Simple integrity check: Does the polygon close?
            if vertices[0] != vertices[-1] and len(vertices) > 2:
                # Most HULC polygons repeat the first point at the end; if not, we note it.
                print("    *Note: Polygon is open (Revit will need a closing line)*")

        except Exception as e:
            print("  !! Error calculating geometry: {}".format(e))

# RUN TEST
run_diagnostic('../EnvolventeCTE--790098c4.json')