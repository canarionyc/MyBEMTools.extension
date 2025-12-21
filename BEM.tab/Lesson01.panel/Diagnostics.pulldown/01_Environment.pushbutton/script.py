# -*- coding: utf-8 -*-
from bem_utils import logger, get_forge_units
from Autodesk.Revit.UI import UIApplication
from Autodesk.Revit.DB import Document
import sys

# PyCharm Hinting
if False:
    # noinspection PyUnreachableCode
    __revit__ = UIApplication()
    doc = Document()

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import SpecTypeId

def check_spec():
    try:
        # This is the internal Forge ID for 'Length'
        test_id = SpecTypeId.Length
        print("Success! Revit found SpecTypeId.Length: {}".format(test_id.TypeId))
    except Exception as e:
        print("Revit Error: {}".format(str(e)))

# noinspection PyUnboundLocalVariable
doc = __revit__.ActiveUIDocument.Document


def run_lesson_1_1():
    logger.info("--- LESSON 1.1: ENVIRONMENT CHECK ---")

    # Check Python Version
    logger.info("Python Version: {}".format(sys.version))

    # Check Revit Version
    version = __revit__.Application.VersionName
    logger.info("Revit Version: {}".format(version))

    # Check Units
    units = get_forge_units(doc)
    logger.info("Project Units: {}".format(units))

    if "Meter" not in units:
        logger.warning("BEM Warning: EnergyPlus prefers Metric. Current: {}".format(units))


if __name__ == "__main__":
    check_spec()
    run_lesson_1_1()