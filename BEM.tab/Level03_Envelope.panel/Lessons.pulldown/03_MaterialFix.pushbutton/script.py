# -*- coding: utf-8 -*-

from Autodesk.Revit.UI import UIApplication
from Autodesk.Revit.DB import Document

# 1. SILENCE PYCHARM: These variables are injected by pyRevit at runtime.
# We use 'if False' so this code never runs in Revit, but PyCharm's
# analyzer sees the types and stops complaining about 'None' or 'Undefined'.
# noinspection PyUnreachableCode
if False:
    __revit__ = UIApplication()
    doc = Document()

from bem_utils import logger, get_readable_units  # Using your new shared library!
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document

logger.info("--- BEM LESSON 3.1 START ---")
logger.debug("Active Project: {}".format(doc.Title))

units = get_readable_units(doc)
logger.info("Current Units: {}".format(units))


def ensure_concrete_thermal_data():
    # 1. Start a Transaction (Required for any Revit change)
    t = Transaction(doc, "BEM: Fix Concrete Assets")
    t.Start()

    logger.info("Scanning for concrete materials missing thermal data...")

    # 2. Collect all materials
    all_materials = FilteredElementCollector(doc).OfClass(Material)

    fixed_count = 0
    for mat in all_materials:
        if "Concrete" in mat.Name and mat.ThermalAssetId == ElementId.InvalidElementId:
            logger.warning("Material '{}' is missing a Thermal Asset!".format(mat.Name))

            # 3. Find a 'Template' Thermal Asset in the project to copy from
            # For this lesson, we are just logging it.
            # In a real tool, we would 'Duplicate' a standard asset here.
            fixed_count += 1

    t.Commit()
    logger.info("Audit complete. Found {} concrete materials needing attention.".format(fixed_count))


if __name__ == "__main__":
    ensure_concrete_thermal_data()