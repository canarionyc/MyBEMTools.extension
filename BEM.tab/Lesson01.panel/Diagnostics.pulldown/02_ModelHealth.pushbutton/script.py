# -*- coding: utf-8 -*-
from bem_utils import logger, get_wall_count
from Autodesk.Revit.UI import UIApplication
from Autodesk.Revit.DB import Document
# 1. This grabs SpatialElement, Wall, FilteredElementCollector, etc.
from Autodesk.Revit.DB import *
# 2. This grabs ONLY Room from the Architecture namespace
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Architecture import Room

if False:
    __revit__ = UIApplication()
    doc = Document()

doc = __revit__.ActiveUIDocument.Document


def run_lesson_1_2():
    logger.info("--- LESSON 1.2: MODEL HEALTH ---")

    # Count Walls
    wall_count = get_wall_count(doc)
    logger.info("Total Walls Found: {}".format(wall_count))

    # Count Rooms (BEM relies on Rooms to define Thermal Zones)
    rooms = FilteredElementCollector(doc).OfClass(SpatialElement).ToElements()
    room_count = len([r for r in rooms if isinstance(r, Room)])

    logger.info("Total Rooms (Thermal Zones) Found: {}".format(room_count))

    if room_count == 0:
        logger.error("BEM CRITICAL: No Rooms found. Energy analysis is impossible without Rooms!")
    else:
        logger.debug("Thermal Zone check passed.")

print(__name__)
run_lesson_1_2()

if __name__ == "__main__":
    run_lesson_1_2()