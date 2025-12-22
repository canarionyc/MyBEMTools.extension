# -*- coding: utf-8 -*-
# noinspection PyUnresolvedReferences
from bem_utils import logger
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import *
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Architecture import *  # Adds Room and SpatialElement support

# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI import UIApplication

# noinspection PyUnresolvedReferences
doc = __revit__.ActiveUIDocument.Document
# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import *


# Heights in Meters (will be converted to Feet internally)
targets = {
    "BEM_Solera": -1.0,
    "BEM_Ground_Level": 0.0,
    "BEM_Living_Ceiling": 4.0,
    "BEM_Roof_Buffer": 4.5
}

t = Transaction(doc, "Align Levels to JSON")
t.Start()

existing_levels = FilteredElementCollector(doc).OfClass(Level).ToElements()

for name, height_m in targets.items():
    height_ft = height_m / 0.3048
    # Try to find existing, or create new
    match = next((l for l in existing_levels if l.Name == name), None)
    if match:
        match.Elevation = height_ft
    else:
        Level.Create(doc, height_ft).Name = name

t.Commit()
print("Levels synchronized with JSON source.")