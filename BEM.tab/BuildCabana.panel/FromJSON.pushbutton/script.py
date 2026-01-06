# -*- coding: utf-8 -*-
import os
# C:\dev\MyBEMTools.extension\...\script.py
from pyrevit import HOST_APP, DB
import sys

# 1. Diagnostic: Check what Revit version actually started
print("RUNNING IN REVIT VERSION: {}".format(HOST_APP.version))

doc = HOST_APP.doc
if doc is None:
    print("CRITICAL ERROR: No document was opened by the CLI.")
    print("This usually means Revit hit an 'Upgrade' or 'Missing Link' dialog.")
    sys.exit(1) # Exit cleanly with an error message instead of crashing


# 1. SETUP
app = HOST_APP.app
# Access the document the CLI just opened for us
model_path = r"C:\RevitAudit\model.rvt"

# 2. HANDLE NEW VS EXISTING
# If the document has no path, or it's just the template,
# save it as our target model name.
if not doc.PathName or ".rte" in doc.PathName.lower():
    print("New project detected. Saving as model.rvt...")
    save_opt = DB.SaveAsOptions()
    save_opt.OverwriteExistingFile = True
    doc.SaveAs(model_path, save_opt)
else:
    print("Opened existing model: {}".format(doc.PathName))

# --- CONTINUE RECONSTRUCTION LOGIC ---
# (Your wall/roof code remains the same, using 'doc')

def to_ft(m):
	return m / 0.3048


# 1. LEVELS FROM JSON
json_levels = {
	"P01 Foundation": -1.0,
	"P02 Ground Floor": 0.0,
	"P03 Attic Floor": 4.0
}

# 2. WINDOW DATA
win_x = 2.5
win_w = 5.0
win_h = 2.2
win_recess = 0.5

with DB.Transaction(doc, "Reconstruct Cabana Final") as t:
	t.Start()

	# Create Levels
	lvls = {}
	for name, elev in json_levels.items():
		new_lvl = DB.Level.Create(doc, to_ft(elev))
		new_lvl.Name = name
		lvls[name] = new_lvl

	# 3. FOOTPRINT (10m South/North x 6m East/West)
	p1 = DB.XYZ(0, 0, 0)
	p2 = DB.XYZ(to_ft(10), 0, 0)
	p3 = DB.XYZ(to_ft(10), to_ft(6), 0)
	p4 = DB.XYZ(0, to_ft(6), 0)

	lines = [DB.Line.CreateBound(p1, p2), DB.Line.CreateBound(p2, p3),
	         DB.Line.CreateBound(p3, p4), DB.Line.CreateBound(p4, p1)]

	# 4. GET TYPES
	wall_type = next((ty for ty in DB.FilteredElementCollector(doc).OfClass(DB.WallType)
	                  if "700" in ty.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()),
	                 next(iter(DB.FilteredElementCollector(doc).OfClass(DB.WallType))))

	roof_type = next(iter(DB.FilteredElementCollector(doc).OfClass(DB.RoofType)), None)

	storefront_type = next((ty for ty in DB.FilteredElementCollector(doc).OfClass(DB.WallType)
	                        if "Storefront" in ty.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()),
	                       None)

	# 5. CREATE WALLS
	south_wall_main = None
	for i, line in enumerate(lines):
		# Crawlspace
		cw = DB.Wall.Create(doc, line, lvls["P01 Foundation"].Id, False)
		cw.get_Parameter(DB.BuiltInParameter.WALL_HEIGHT_TYPE).Set(lvls["P02 Ground Floor"].Id)

		# Main Floor
		mw = DB.Wall.Create(doc, line, lvls["P02 Ground Floor"].Id, False)
		mw.get_Parameter(DB.BuiltInParameter.WALL_HEIGHT_TYPE).Set(lvls["P03 Attic Floor"].Id)
		if i == 0: south_wall_main = mw

	# 6. CREATE ROOF (IronPython Tuple Handling)
	footprint_array = DB.CurveArray()
	for l in lines: footprint_array.Append(l)

	# OMIT the out_curves parameter. IronPython returns it in a tuple.
	# Result: (FootPrintRoof, ModelCurveArray)
	roof, out_curves = doc.Create.NewFootPrintRoof(footprint_array, lvls["P03 Attic Floor"], roof_type)

	# Set the 0.5m Attic wall height
	roof.get_Parameter(DB.BuiltInParameter.ROOF_LEVEL_OFFSET_PARAM).Set(to_ft(0.5))

	# Apply 45 deg slope
	# We want Gables on South (i=0) and North (i=2)
	# Pitch on East (i=1) and West (i=3)
	for i, mc in enumerate(out_curves):
		if i % 2 == 0:  # 0 and 2 (South/North)
			roof.set_DefinesSlope(mc, False)
		else:  # 1 and 3 (East/West)
			roof.set_DefinesSlope(mc, True)
			roof.set_SlopeAngle(mc, 1.0)  # 45 degrees

	# 7. CREATE RECESSED WINDOW
	win_start = DB.XYZ(to_ft(win_x), to_ft(win_recess), to_ft(0.5))
	win_end = DB.XYZ(to_ft(win_x + win_w), to_ft(win_recess), to_ft(0.5))
	win_line = DB.Line.CreateBound(win_start, win_end)

	curtain_wall = DB.Wall.Create(doc, win_line, storefront_type.Id, lvls["P02 Ground Floor"].Id, to_ft(win_h), 0,
	                              False, False)
	DB.WallUtils.EmbedWallIntoHostWall(curtain_wall, south_wall_main)

	t.Commit()

print("Cabana reconstructed! Check the 3D view for the 0.5m recess and 45 degree roof.")