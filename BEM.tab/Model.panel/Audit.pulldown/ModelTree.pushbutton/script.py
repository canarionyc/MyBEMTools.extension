# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script

doc = revit.doc
output = script.get_output()

# Unit Conversion factor (Feet to Meters)
FT_TO_M = 0.3048

print("--- OBSESSIVE BEM LEVEL AUDIT (METRIC) ---")

# 1. Collect all levels
levels = DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements()
sorted_levels = sorted(levels, key=lambda l: l.Elevation)

# 2. Collect ALL model elements once to check dependencies
# We exclude types and keep only instances to find what's actually in the model
all_elements = DB.FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()

print("Found {} total levels. Analyzing dependencies for each...\n".format(len(sorted_levels)))

for level in sorted_levels:
    elev_m = level.Elevation * FT_TO_M
    print("=" * 60)
    print("LEVEL: [{}]".format(level.Name))
    print("ELEVATION: {:.4f} m".format(elev_m))
    print("-" * 60)

    # Find elements associated with this level
    # We check the LevelId property which is the primary dependency
    dependencies = []
    for el in all_elements:
        if el.LevelId == level.Id:
            dependencies.append(el)

    if not dependencies:
        print("  [SAFE] No model elements are hosted on this level.")
    else:
        print("  [WARNING] {} Elements depend on this level:".format(len(dependencies)))
        
        # Categorize dependencies for readability
        dep_map = {}
        for d in dependencies:
            cat = d.Category.Name if d.Category else "Other"
            if cat not in dep_map:
                dep_map[cat] = []
            dep_map[cat].append(d)

        for cat_name, items in dep_map.items():
            print("    > {}: {} items".format(cat_name, len(items)))
            # List first 5 items of each category as examples
            for item in items[:5]:
                name = item.Name if hasattr(item, "Name") else "Unnamed"
                print("      - {} (ID: {})".format(name, item.Id))
            if len(items) > 5:
                print("      - ... and {} more".format(len(items) - 5))

    # 3. Check for associated Views (the "10 views" in your warning)
    # Views often depend on levels but don't always use the .LevelId property
    views = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()
    level_views = [v for v in views if not v.IsTemplate and hasattr(v, "GenLevel") and v.GenLevel and v.GenLevel.Id == level.Id]
    
    if level_views:
        print("\n  [VIEW DEPENDENCIES] {} Views will be deleted:".format(len(level_views)))
        for v in level_views:
            print("    * View: {} ({})".format(v.Name, v.ViewType))

print("\n" + "=" * 60)
print("AUDIT COMPLETE")