#! python3
# -*- coding: utf-8 -*-

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
import Autodesk.Revit.DB as DB

# --- CONFIGURATION ---
LEVEL_NAME = "GARDEN"
ELEVATION_METERS = -1.0
M_TO_FT = 1.0 / 0.3048

def move_solera_to_garden():
    # Access the active document
    uidoc = __revit__.ActiveUIDocument
    doc = uidoc.Document
    
    # 1. Get currently selected elements in the UI
    selection_ids = uidoc.Selection.GetElementIds()
    selected_floors = [doc.GetElement(eid) for eid in selection_ids if isinstance(doc.GetElement(eid), DB.Floor)]
    
    if not selected_floors:
        print("⚠️ Please select a floor (solera) in Revit before running this script.")
        return

    # 2. Check if the Level already exists
    existing_levels = DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements()
    garden_level = next((l for l in existing_levels if l.Name == LEVEL_NAME), None)

    t = DB.Transaction(doc, "Create Garden Level and Move Floor")
    t.Start()
    
    try:
        # 3. Create the Level if it doesn't exist
        if not garden_level:
            elev_ft = ELEVATION_METERS * M_TO_FT
            garden_level = DB.Level.Create(doc, elev_ft)
            garden_level.Name = LEVEL_NAME
            print(f"✅ Created Level: {LEVEL_NAME} at {ELEVATION_METERS}m")
        else:
            print(f"ℹ️ Using existing Level: {LEVEL_NAME}")

        # 4. Move the first selected floor to the new level
        target_floor = selected_floors[0]
        
        # Change the Level property (re-hosting)
        # In the API, we use the BuiltInParameter 'LEVEL_PARAM' to change hosting
        param = target_floor.get_Parameter(DB.BuiltInParameter.LEVEL_PARAM)
        if param:
            param.Set(garden_level.Id)
            
            # Reset any 'Height Offset From Level' to 0 so it sits flush on the new level
            offset_param = target_floor.get_Parameter(DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)
            if offset_param:
                offset_param.Set(0.0)
                
            print(f"✅ Moved Floor [{target_floor.Id}] to {LEVEL_NAME}")

        t.Commit()
    except Exception as e:
        t.RollBack()
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    move_solera_to_garden()