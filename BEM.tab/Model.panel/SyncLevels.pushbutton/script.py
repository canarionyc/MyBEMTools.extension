#! python3
import json
import os
import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

# --- CONFIGURATION ---
RULES_PATH = r"C:\dev\MyBEMTools.extension\bem_api\data\rules.json"
MM_TO_FT = 0.0032808399  # Strict internal unit conversion

def to_ft(mm_val):
    return float(mm_val) * MM_TO_FT

def sync_levels_only():
    doc = __revit__.ActiveUIDocument.Document

    if not os.path.exists(RULES_PATH):
        print("❌ ERROR: rules.json not found.")
        return

    with open(RULES_PATH, 'r', encoding='utf-8') as f:
        rules = json.load(f)

    rules_levels = rules.get("levels", {})
    if not rules_levels:
        print("⚠️ No levels found in rules.json.")
        return

    print("🚀 Starting Level Sync...")

    # 1. Get existing levels to avoid duplicates
    existing_levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
    existing_names = [lvl.Name for lvl in existing_levels]

    # 2. Open Transaction to Create Levels
    t = Transaction(doc, "Sync BEM Levels Only")
    t.Start()
    
    created_count = 0
    for name, data in rules_levels.items():
        if name not in existing_names:
            elev_ft = to_ft(data.get("elevation", 0))
            new_lvl = Level.Create(doc, elev_ft)
            new_lvl.Name = name
            print("✅ Created Level: {} at {} mm".format(name, data.get('elevation', 0)))
            created_count += 1
        else:
            print("⏩ Skipped: {} (Already exists)".format(name))
            
    t.Commit()
    
    print("\n🎉 Done! Created {} missing levels.".format(created_count))

if __name__ == "__main__":
    sync_levels_only()