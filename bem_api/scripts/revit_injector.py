#! python3
import json
import os
import sys
import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

# --- CONFIGURATION ---
PAYLOAD_PATH = r"C:\dev\MyBEMTools.extension\bem_api\output\payload.json"
RULES_PATH = r"C:\dev\MyBEMTools.extension\bem_api\data\rules.json"
MM_TO_FT = 0.0032808399  # Strict Revit internal unit conversion

# Map Rhino text to Revit Built-in Integer for Wall Location Line
LOCATION_LINE_MAP = {
    "WallCenterline": 0,
    "CoreCenterline": 1,
    "FinishFaceExterior": 2,
    "FinishFaceInterior": 3
}

def to_ft(mm_val):
    return float(mm_val) * MM_TO_FT

def to_xyz(pt):
    return XYZ(to_ft(pt[0]), to_ft(pt[1]), 0) # Z is handled by Levels/Offsets

def get_or_create_levels(doc, rules_levels):
    """Silently creates missing levels and returns a {name: Level} dictionary."""
    level_dict = {}
    
    # 1. Get existing levels
    existing_levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
    for lvl in existing_levels:
        level_dict[lvl.Name] = lvl

    # 2. Create missing levels in a dedicated preliminary transaction
    t = Transaction(doc, "Sync BEM Levels")
    t.Start()
    for name, data in rules_levels.items():
        if name not in level_dict:
            elev_ft = to_ft(data.get("elevation", 0))
            new_lvl = Level.Create(doc, elev_ft)
            new_lvl.Name = name
            level_dict[name] = new_lvl
    t.Commit()
    
    return level_dict

def get_type_dictionary(doc, rule_types):
    """Builds dictionaries mapping family names to their Revit ElementIds."""
    type_maps = {"Wall": {}, "Floor": {}, "Roof": {}}
    
    # Collect all types
    wall_types = FilteredElementCollector(doc).OfClass(WallType).ToElements()
    floor_types = FilteredElementCollector(doc).OfClass(FloorType).ToElements()
    roof_types = FilteredElementCollector(doc).OfClass(RoofType).ToElements()

    # Map them by their name
    for wt in wall_types: type_maps["Wall"][wt.LookupParameter("Type Name").AsString()] = wt
    for ft in floor_types: type_maps["Floor"][ft.LookupParameter("Type Name").AsString()] = ft
    for rt in roof_types: type_maps["Roof"][rt.LookupParameter("Type Name").AsString()] = rt
        
    return type_maps

def generate_bem_model():
    doc = __revit__.ActiveUIDocument.Document

    # 1. LOAD DATA
    if not os.path.exists(PAYLOAD_PATH) or not os.path.exists(RULES_PATH):
        print("❌ ERROR: JSON files not found.")
        return

    with open(PAYLOAD_PATH, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    with open(RULES_PATH, 'r', encoding='utf-8') as f:
        rules = json.load(f)

    print("🚀 Starting BEM Injection Engine...")

    # 2. PRE-FLIGHT: SYNC LEVELS & TYPES
    levels = get_or_create_levels(doc, rules.get("levels", {}))
    type_dicts = get_type_dictionary(doc, rules.get("types", {}))

    # 3. OPEN MASTER TRANSACTION GROUP
    tg = TransactionGroup(doc, "Generate BEM Model")
    tg.Start()

    success_count = 0
    fail_count = 0

    # 4. INJECTION LOOP
    for i, item in enumerate(payload):
        category = item.get("category", "")
        rule = rules["types"].get(category, {})
        coords = item.get("coordinates", [])
        
        if len(coords) < 2:
            continue

        level_name = item.get("level")
        base_level = levels.get(level_name)
        if not base_level:
            continue

        base_offset_ft = to_ft(item.get("base_offset", rule.get("base_offset", 0)))

        # ⚡ OPEN MICRO-TRANSACTION
        t = Transaction(doc, f"Create {category} {i}")
        t.Start()

        try:
            # ==========================================
            # WALL GENERATION
            # ==========================================
            if not rule.get("is_floor"):
                type_name = item.get("family_name", rule.get("family_name"))
                wall_type = type_dicts["Wall"].get(type_name)
                
                # Create the Line
                start_pt = to_xyz(coords[0])
                end_pt = to_xyz(coords[1])
                line = Line.CreateBound(start_pt, end_pt)

                # Create Wall
                wall = Wall.Create(doc, line, wall_type.Id, base_level.Id, 10.0, base_offset_ft, False, False)

                # Set Location Line
                loc_string = item.get("location_line", rule.get("location_line", "WallCenterline"))
                loc_int = LOCATION_LINE_MAP.get(loc_string, 0)
                wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(loc_int)

                # Handle Top Constraint
                top_lvl_name = item.get("top_level")
                if top_lvl_name and top_lvl_name in levels:
                    wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(levels[top_lvl_name].Id)
                
                wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).Set(base_offset_ft)

            # ==========================================
            # FLOOR & ROOF GENERATION (Polylines)
            # ==========================================
            else:
                is_roof = "ROOF" in category.upper()
                is_foundation = "FOUNDATION" in category.upper()

                # Build CurveLoop (for floors) and CurveArray (for roofs)
                curve_loop = CurveLoop()
                curve_array = CurveArray()
                
                for j in range(len(coords)):
                    pt1 = to_xyz(coords[j])
                    pt2 = to_xyz(coords[(j + 1) % len(coords)]) # Wrap to start
                    if pt1.DistanceTo(pt2) > 0.01: # Avoid microscopic lines
                        bound_line = Line.CreateBound(pt1, pt2)
                        curve_loop.Append(bound_line)
                        curve_array.Append(bound_line)

                # Create Roof
                if is_roof:
                    type_name = item.get("floor_type", rule.get("floor_type"))
                    roof_type = type_dicts["Roof"].get(type_name)
                    
                    # Create Map (needed for FootPrintRoof)
                    mapping = doc.Application.Create.NewModelCurveArray()
                    roof = doc.Create.NewFootPrintRoof(curve_array, base_level, roof_type, out_mapping=mapping)
                    
                    # Force it to be completely flat
                    for edge in mapping:
                        roof.set_DefinesSlope(edge, False)
                        
                    roof.get_Parameter(BuiltInParameter.ROOF_BASE_LEVEL_OFFSET_PARAM).Set(base_offset_ft)

                # Create Floor or Foundation
                else:
                    type_name = item.get("floor_type", rule.get("floor_type"))
                    floor_type = type_dicts["Floor"].get(type_name)
                    
                    # Revit 2022+ Floor Creation method
                    # (Uses a List of CurveLoops)
                    import System.Collections.Generic
                    loop_list = System.Collections.Generic.List[CurveLoop]()
                    loop_list.Add(curve_loop)
                    
                    structural = True if is_foundation else False
                    
                    floor = Floor.Create(doc, loop_list, floor_type.Id, base_level.Id)
                    
                    # If it's a foundation, ensure Structural Usage is checked
                    if is_foundation:
                        floor.get_Parameter(BuiltInParameter.FLOOR_PARAM_IS_STRUCTURAL).Set(1)
                    
                    floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(base_offset_ft)

            # ⚡ COMMIT MICRO-TRANSACTION IF SUCCESSFUL
            t.Commit()
            success_count += 1

        except Exception as e:
            # ⚡ ROLLBACK ON FAILURE
            t.RollBack()
            print(f"⚠️ Warning: Failed to generate {category} at Level {level_name}. Error: {e}")
            fail_count += 1

    # 5. ASSIMILATE MASTER TRANSACTION
    tg.Assimilate()
    
    print("\n✅ BEM Generation Complete!")
    print(f"📊 Successfully built: {success_count} elements.")
    if fail_count > 0:
        print(f"⚠️ Skipped {fail_count} elements due to geometric errors.")

if __name__ == "__main__":
    generate_bem_model()