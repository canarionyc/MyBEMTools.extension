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
from bem_utils import logger, get_readable_units
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document

logger.info("--- BEM LESSON 3.1 START ---")
logger.debug("Active Project: {}".format(doc.Title))

units = get_readable_units(doc)
logger.info("Current Units: {}".format(units))

def audit_basement_walls():
    # Find all walls
    walls = FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType()

    logger.info("--- 🕳️ BASEMENT GROUND-COUPLING AUDIT ---")

    for wall in walls:
        # Get the height of the bottom of the wall
        base_offset = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
        base_level_id = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT).AsElementId()
        base_level = doc.GetElement(base_level_id)

        # Check if the level name suggests it's a basement
        level_name = base_level.Name.lower()

        if "basement" in level_name or "level -1" in level_name:
            logger.info("Wall {} (ID: {}) is GROUND-COUPLED.".format(wall.Name, wall.Id))
            # In the future, we will flag this wall for the 'GroundDomain' in OpenStudio
        else:
            logger.debug("Wall {} is exposed to Air.".format(wall.Id))


if __name__ == "__main__":
    audit_basement_walls()
