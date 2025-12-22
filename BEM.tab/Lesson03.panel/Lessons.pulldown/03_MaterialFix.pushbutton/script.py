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

# -*- coding: utf-8 -*-
# noinspection PyUnresolvedReferences
from bem_utils import logger
from Autodesk.Revit.DB import *

# Standard Boilerplate
# noinspection PyUnboundLocalVariable
doc = __revit__.ActiveUIDocument.Document


def run_fixer():
    logger.info("--- 💉 BEM: MATERIAL THERMAL INJECTOR ---")

    # 1. Collect all materials in the document
    materials = FilteredElementCollector(doc).OfClass(Material).ToElements()

    # 2. Find a "Template" Thermal Asset
    # We look for a material that DEFINITELY has data to use as a donor
    template_asset_id = None
    for mat in materials:
        if mat.ThermalAssetId != ElementId.InvalidElementId:
            template_asset_id = mat.ThermalAssetId
            break

    if not template_asset_id:
        logger.error("No Thermal Assets found in project to use as a template!")
        return

    # 3. Apply the fix
    t = Transaction(doc, "BEM: Inject Thermal Assets")
    t.Start()

    fix_count = 0
    try:
        for mat in materials:
            # Check if it's missing the Thermal tab
            if mat.ThermalAssetId == ElementId.InvalidElementId:
                # Logic: Only fix materials actually used in Walls/Floors (optional filter)
                # For now, we fix anything with "Concrete", "Masonry", or "Brick" in the name
                name = mat.Name.lower()
                if any(x in name for x in ["concrete", "brick", "stone", "masonry", "insulation"]):
                    # INJECT: Assign the template asset to this material
                    mat.ThermalAssetId = template_asset_id
                    logger.info("Fixed: Added Thermal Asset to {}".format(mat.Name))
                    fix_count += 1

        t.Commit()
        logger.info("SUCCESS: Injected thermal data into {} materials.".format(fix_count))

    except Exception as e:
        t.RollBack()
        logger.error("Fixer failed: {}".format(str(e)))


if __name__ == "__main__":
    run_fixer()