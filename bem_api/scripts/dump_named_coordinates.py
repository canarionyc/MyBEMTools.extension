import rhinoscriptsyntax as rs

def dump_named_coordinates():
    print("--- COORDINATE REPORT ---")
    
    points = rs.ObjectsByType(rs.filter.point)
    if points:
        print("\n>> POINTS IN MODEL:")
        for pt in points:
            coords = rs.PointCoordinates(pt)
            name = rs.ObjectName(pt)
            
            # Si el punto no tiene nombre, le ponemos una etiqueta por defecto
            display_name = name if name else "Unnamed Point"
            
            print("{}: ({:.2f}, {:.2f}, {:.2f})".format(display_name, coords.X, coords.Y, coords.Z))
    else:
        print("\n>> No points found.")
        
dump_named_coordinates()