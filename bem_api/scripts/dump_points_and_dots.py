import rhinoscriptsyntax as rs

def dump_coordinates():
    print("--- COORDINATE REPORT ---")
    
    # 1. Find and print all bare Points
    points = rs.ObjectsByType(rs.filter.point)
    if points:
        print("\n>> POINTS IN MODEL:")
        for i, pt in enumerate(points):
            coords = rs.PointCoordinates(pt)
            print("Point {}: ({:.2f}, {:.2f}, {:.2f})".format(i+1, coords.X, coords.Y, coords.Z))
    else:
        print("\n>> No points found.")

    # 2. Find and print all Text Dots
    dots = rs.ObjectsByType(rs.filter.textdot)
    if dots:
        print("\n>> LABELS (TEXT DOTS):")
        for dot in dots:
            text = rs.TextDotText(dot)
            coords = rs.TextDotPoint(dot)
            print("Label '{}': ({:.2f}, {:.2f}, {:.2f})".format(text, coords.X, coords.Y, coords.Z))
    else:
        print("\n>> No labels found.")
        
dump_coordinates()