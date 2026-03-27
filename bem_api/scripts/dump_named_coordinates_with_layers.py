import rhinoscriptsyntax as rs

def dump_named_coordinates_with_layers():
    print("--- DETAILED COORDINATE REPORT ---")
    
    # Get all points in the document
    points = rs.ObjectsByType(rs.filter.point)
    
    if points:
        print("\n{:<15} | {:<25} | {:<15}".format("NAME", "COORDINATES (X, Y, Z)", "LAYER"))
        print("-" * 65)
        
        for pt in points:
            coords = rs.PointCoordinates(pt)
            name = rs.ObjectName(pt)
            layer = rs.ObjectLayer(pt)
            
            # Formatting the display
            display_name = name if name else "Unnamed"
            coord_str = "({:.2f}, {:.2f}, {:.2f})".format(coords.X, coords.Y, coords.Z)
            
            print("{:<15} | {:<25} | {:<15}".format(display_name, coord_str, layer))
    else:
        print("\n>> No points found in the model.")

dump_named_coordinates_with_layers()