# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *
from pyrevit import revit

doc = revit.doc

# Start a safe transaction to delete the elements
with revit.Transaction("Wipe All DirectShapes"):
    # Collect every single DirectShape in the database
    ds_ids = FilteredElementCollector(doc).OfClass(DirectShape).ToElementIds()
    
    if ds_ids:
        for e_id in ds_ids:
            doc.Delete(e_id)
        print("SUCCESS: Deleted {} DirectShapes from the database.".format(len(ds_ids)))
    else:
        print("No DirectShapes found to delete.")