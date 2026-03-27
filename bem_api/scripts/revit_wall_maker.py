import clr
import os
import traceback
import logging

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (Level, UnitUtils, UnitTypeId, XYZ, Line, Wall, 
                               FilteredElementCollector, BuiltInCategory, Structure,
                               BuiltInParameter)
from pyrevit import revit

# --- SETUP ROBUST LOGGING ---
LOG_DIR = r"C:\Users\tglla\AppData\Roaming\BEM_API"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
LOG_FILE = os.path.join(LOG_DIR, "wall_maker.log")

logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filemode='w') # 'w' overwrites the log each time so it's clean
logging.info("--- STARTED WALL MAKER SCRIPT ---")

try:
    # The listener automatically provides 'data', 'doc', and 'result'
    ext_walls_data = data.get('exterior_walls', [])
    int_walls_data = data.get('interior_walls', [])
    doors_data = data.get('doors', [])

    walls_created_count = 0
    doors_created_count = 0
    built_walls = []

    with revit.Transaction("BEM: Create CAD Walls and Doors"):
        
        # --- 1. FIND SPECIFIC LEVELS ---
        all_levels = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()
        
        # Log all found levels to the file
        level_names = [l.Name for l in all_levels]
        logging.info("Found {} levels in model: {}".format(len(level_names), ", ".join(level_names)))
        
        base_level = next((l for l in all_levels if l.Name == "INTERIOR"), None)
        top_level = next((l for l in all_levels if l.Name == "PISO_CUBIERTA"), None)
        
        if not base_level:
            raise Exception("CRITICAL ERROR: 'INTERIOR' level not found. Available levels: {}".format(level_names))
        if not top_level:
            raise Exception("CRITICAL ERROR: 'PISO_CUBIERTA' level not found. Available levels: {}".format(level_names))

        logging.info("Successfully matched Base Level: ID {}".format(base_level.Id))
        logging.info("Successfully matched Top Level: ID {}".format(top_level.Id))

        # --- 2. FIND SPECIFIC WALL TYPES ---
        all_wall_types = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsElementType().ToElements()
        
        ext_wall_type = None
        int_wall_type = None
        
        # Safely loop through wall types, ignoring weird system elements
        for wt in all_wall_types:
            try:
                # getattr safely returns an empty string if the property is missing
                name = getattr(wt, "Name", "") 
                if not name: 
                    continue
                
                if "20" in name and "cm" in name and not ext_wall_type:
                    ext_wall_type = wt
                elif "10" in name and "cm" in name and not int_wall_type:
                    int_wall_type = wt
            except Exception:
                continue # Skip elements that cause errors
        
        # Fallbacks
        if not ext_wall_type: ext_wall_type = all_wall_types[0]
        if not int_wall_type: int_wall_type = all_wall_types[0]

        logging.info("Using Ext Wall: {}".format(getattr(ext_wall_type, "Name", "Unknown")))
        logging.info("Using Int Wall: {}".format(getattr(int_wall_type, "Name", "Unknown")))

        # --- 3. FIND SPECIFIC DOOR TYPES ---
        all_door_types = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsElementType().ToElements()
        if not all_door_types:
            raise Exception("CRITICAL ERROR: No Door Families are loaded.")

        # --- 4. BUILD EXTERIOR WALLS ---
        logging.info("Building {} exterior walls...".format(len(ext_walls_data)))
        for wall_data in ext_walls_data:
            x1 = UnitUtils.ConvertToInternalUnits(float(wall_data['start'][0]), UnitTypeId.Millimeters)
            y1 = UnitUtils.ConvertToInternalUnits(float(wall_data['start'][1]), UnitTypeId.Millimeters)
            x2 = UnitUtils.ConvertToInternalUnits(float(wall_data['end'][0]), UnitTypeId.Millimeters)
            y2 = UnitUtils.ConvertToInternalUnits(float(wall_data['end'][1]), UnitTypeId.Millimeters)
            
            pt1 = XYZ(x1, y1, 0)
            pt2 = XYZ(x2, y2, 0)
            
            if pt1.DistanceTo(pt2) > 0.1:
                line = Line.CreateBound(pt1, pt2)
                new_wall = Wall.Create(doc, line, ext_wall_type.Id, base_level.Id, 10.0, 0.0, False, False)
                
                if top_level:
                    top_param = new_wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)
                    if top_param:
                        top_param.Set(top_level.Id)
                        
                built_walls.append(new_wall)
                walls_created_count += 1

        # --- 5. BUILD INTERIOR WALLS ---
        logging.info("Building {} interior walls...".format(len(int_walls_data)))
        for wall_data in int_walls_data:
            x1 = UnitUtils.ConvertToInternalUnits(float(wall_data['start'][0]), UnitTypeId.Millimeters)
            y1 = UnitUtils.ConvertToInternalUnits(float(wall_data['start'][1]), UnitTypeId.Millimeters)
            x2 = UnitUtils.ConvertToInternalUnits(float(wall_data['end'][0]), UnitTypeId.Millimeters)
            y2 = UnitUtils.ConvertToInternalUnits(float(wall_data['end'][1]), UnitTypeId.Millimeters)
            
            pt1 = XYZ(x1, y1, 0)
            pt2 = XYZ(x2, y2, 0)
            
            if pt1.DistanceTo(pt2) > 0.1:
                line = Line.CreateBound(pt1, pt2)
                new_wall = Wall.Create(doc, line, int_wall_type.Id, base_level.Id, 10.0, 0.0, False, False)
                
                if top_level:
                    top_param = new_wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)
                    if top_param:
                        top_param.Set(top_level.Id)
                        
                built_walls.append(new_wall)
                walls_created_count += 1

        # --- 6. PLACE DOORS ---
        logging.info("Placing {} doors...".format(len(doors_data)))
        for door in doors_data:
            dx = UnitUtils.ConvertToInternalUnits(float(door['location'][0]), UnitTypeId.Millimeters)
            dy = UnitUtils.ConvertToInternalUnits(float(door['location'][1]), UnitTypeId.Millimeters)
            door_pt = XYZ(dx, dy, 0)
            
            req_type = door.get('type', '')
            door_type = None
            
            # Safely search for the exact door type
            for dt in all_door_types:
                try:
                    dt_name = getattr(dt, "Name", "")
                    dt_family = getattr(dt, "FamilyName", "")
                    if req_type in dt_name or req_type in dt_family:
                        door_type = dt
                        break
                except Exception:
                    continue
            
            # Fuzzy fallback: look for ANY double door
            if not door_type:
                for dt in all_door_types:
                    try:
                        dt_name = getattr(dt, "Name", "")
                        if "Double" in dt_name or "Doble" in dt_name:
                            door_type = dt
                            break
                    except Exception:
                        continue
            
            # Absolute fallback: just grab the first door available
            if not door_type:
                door_type = all_door_types[0]
                
            if not door_type.IsActive:
                door_type.Activate()
            
            host_wall = None
            for w in built_walls:
                curve = w.Location.Curve
                intersection = curve.Project(door_pt)
                
                if intersection and intersection.Distance < 0.01:
                    host_wall = w
                    break
            
            if host_wall:
                doc.Create.NewFamilyInstance(door_pt, door_type, host_wall, base_level, Structure.StructuralType.NonStructural)
                doors_created_count += 1

    # Populate success response
    result['status'] = 'Success'
    result['message'] = 'Created {} walls and {} doors.'.format(walls_created_count, doors_created_count)
    result['project'] = doc.Title
    logging.info("SUCCESS: Created {} walls and {} doors.".format(walls_created_count, doors_created_count))

except Exception as e:
    # CAPTURE EXACT LINE NUMBER AND STACK TRACE
    error_trace = traceback.format_exc()
    logging.error("FATAL SCRIPT ERROR:\n" + error_trace)
    
    # Send the full stack trace back to the terminal payload
    result['status'] = 'error'
    result['details'] = error_trace