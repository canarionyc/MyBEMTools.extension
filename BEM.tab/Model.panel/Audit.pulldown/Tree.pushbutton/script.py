# -*- coding: utf-8 -*-
import sys
import os
import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from pyrevit import revit

# Unit Conversion factors
FT_TO_M = 0.3048
FT_TO_MM = 304.8


def log(msg, error=False):
    """Robust logger that forces output to the console immediately"""
    stream = sys.stderr if error else sys.stdout
    stream.write("--- [BEM LOG]: {} ---\n".format(msg))
    stream.flush()


log("PROCESS STARTED")

# 1. Document Acquisition (Headless & UI Fallback)
doc = None
try:
    if '__models__' in globals() and __models__:
        model_path = __models__[0]
        log("Opening model headlessly: {}".format(model_path))
        doc = revit.app.OpenDocumentFile(model_path)

    if not doc:
        doc = revit.doc  # Fallback for standard pyRevit UI execution

    if doc:
        log("Successfully linked to: {}".format(doc.Title))
    else:
        log("FATAL: No document could be acquired.", True)
        sys.exit(1)
except Exception as e:
    log("Initialization Error: {}".format(e), True)
    sys.exit(1)

# 2. Collect targeted elements
levels = FilteredElementCollector(doc).OfCategory(
    BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()
sorted_levels = sorted(levels, key=lambda l: l.Elevation)

walls = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType().ToElements()
doors = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType().ToElements()

# NEW: Collect all DirectShapes
direct_shapes = FilteredElementCollector(doc).OfClass(DirectShape).ToElements()

log("\n" + "=" * 60)
log(" BEM MODEL AUDIT TREE: " + doc.Title)
log(" Found: {} Levels, {} Walls, {} Doors, {} DirectShapes".format(len(sorted_levels), len(walls), len(doors), len(direct_shapes)))
log("=" * 60)

# 3. Build and Print the Tree
for level in sorted_levels:
    elev_m = level.Elevation * FT_TO_M
    log("\nLEVEL: [{}] (Elevation: {:.2f} m)".format(level.Name, elev_m))
    log("-" * 60)

    # Filter walls and doors hosted on this specific level
    level_walls = [w for w in walls if w.LevelId == level.Id]
    level_doors = [d for d in doors if d.LevelId == level.Id]

    if not level_walls and not level_doors:
        log("  [Empty Level]")
        continue

    if level_walls:
        log("  > WALLS ({}):".format(len(level_walls)))
        for w in level_walls:
            curve = w.Location.Curve if w.Location else None
            if curve:
                pt1 = curve.GetEndPoint(0)
                pt2 = curve.GetEndPoint(1)
                # Convert back to MM to match the JSON payload
                x1, y1 = pt1.X * FT_TO_MM, pt1.Y * FT_TO_MM
                x2, y2 = pt2.X * FT_TO_MM, pt2.Y * FT_TO_MM
                log("    - Wall ID {}: Start({:.1f}, {:.1f}) to End({:.1f}, {:.1f}) mm".format(w.Id, x1, y1, x2, y2))
            else:
                log("    - Wall ID {} (No accessible curve)".format(w.Id))

    if level_doors:
        log("  > DOORS ({}):".format(len(level_doors)))
        for d in level_doors:
            pt = d.Location.Point if d.Location else None
            if pt:
                x, y = pt.X * FT_TO_MM, pt.Y * FT_TO_MM
                log("    - Door ID {}: Location({:.1f}, {:.1f}) mm".format(d.Id, x, y))
            else:
                log("    - Door ID {}".format(d.Id))

# NEW: Unhosted Elements / DirectShapes Tree
log("\n" + "=" * 60)
log("UNHOSTED ELEMENTS & DIRECTSHAPES")
log("-" * 60)

if not direct_shapes:
    log("  [No DirectShapes Found]")
else:
    for ds in direct_shapes:
        cat_name = ds.Category.Name if ds.Category else "Unknown Category"
        name = ds.Name
        
        # We use BoundingBox because DirectShapes don't typically have Location curves
        bbox = ds.get_BoundingBox(None)
        if bbox:
            # Convert center from internal feet to meters for readability
            cx = ((bbox.Min.X + bbox.Max.X) / 2.0) * FT_TO_M
            cy = ((bbox.Min.Y + bbox.Max.Y) / 2.0) * FT_TO_M
            cz = ((bbox.Min.Z + bbox.Max.Z) / 2.0) * FT_TO_M
            log("  > [{}] {} (ID: {}) | Center: ({:.2f}, {:.2f}, {:.2f}) m".format(cat_name, name, ds.Id, cx, cy, cz))
        else:
            log("  > [{}] {} (ID: {}) | No BoundingBox".format(cat_name, name, ds.Id))

log("\n" + "=" * 60)
log("AUDIT COMPLETE")