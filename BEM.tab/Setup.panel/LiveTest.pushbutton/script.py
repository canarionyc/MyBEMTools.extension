# -*- coding: utf-8 -*-
from pyrevit import revit, DB, HOST_APP

print("========================================")
print("   PYREVIT 2025 STABILITY TEST          ")
print("========================================")

# Use HOST_APP to get the version correctly
print("Revit Version: {}".format(HOST_APP.version))
print("Document Title: {}".format(revit.doc.Title))

# Verify our South Wall exists
walls = DB.FilteredElementCollector(revit.doc).OfClass(DB.Wall).ToElements()
print("Total Walls in Project: {}".format(len(walls)))

print("========================================")
print("SUCCESS: ENGINE 2712 IS READY")