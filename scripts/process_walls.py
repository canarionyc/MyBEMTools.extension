
from global_vertices import get_global_vertices

# Test with your sample
sample_wall = {
    'geometry': {
        'azimuth': 0,
        'tilt': 90,
        'position': [0, 0, -1],
        'polygon': [[0, 0], [8, 0], [8, 1], [0, 1]]
    }
}

vertices = get_global_vertices(sample_wall)
print("3D Vertices for Revit:")
for i, pt in enumerate(vertices):
    print("Point {}: {}".format(i, pt))