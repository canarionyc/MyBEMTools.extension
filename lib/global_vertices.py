import math


def get_global_vertices(wall_json):
    geom = wall_json['geometry']
    pos = geom['position']
    # EnvolventeCTE Azimuth: 0=S, 90=E, 180=N, 270=W
    # Convert to radians and adjust for Cartesian (Revit) coordinates
    # In Revit, we want Azimuth 0 (South) to result in a vector pointing (1,0,0)
    az_rad = math.radians(geom['azimuth'])
    tilt_rad = math.radians(geom['tilt'])

    # 1. Calculate Basis Vectors
    # Horizontal vector along the wall face
    vx = [math.cos(az_rad), -math.sin(az_rad), 0]

    # Vertical/Tilt vector
    # For Tilt 90 (Vertical), this is just [0,0,1]
    # For Roofs (Tilt < 90), this involves Z and horizontal components
    vy = [
        math.sin(az_rad) * math.cos(tilt_rad),
        math.cos(az_rad) * math.cos(tilt_rad),
        math.sin(tilt_rad)
    ]

    global_pts = []
    for px, py in geom['polygon']:
        gx = pos[0] + (px * vx[0]) + (py * vy[0])
        gy = pos[1] + (px * vx[1]) + (py * vy[1])
        gz = pos[2] + (px * vx[2]) + (py * vy[2])
        global_pts.append((round(gx, 3), round(gy, 3), round(gz, 3)))

    return global_pts