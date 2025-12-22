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
from bem_utils import logger, SQFT_TO_M2
from Autodesk.Revit.DB import *


# noinspection PyUnresolvedReferences
doc = __revit__.ActiveUIDocument.Document

def run_script():
    logger.info("--- BEM GEOMETRY: SI CONVERSION ---")

    walls = FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType()

    for wall in walls:
        # 1. Get Area (Always returns Square Feet from API)
        area_internal = wall.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED).AsDouble()

        # 2. Convert to BEM Standard (Square Meters)
        area_m2 = area_internal * SQFT_TO_M2

        logger.info("Wall {}: Area = {:.4f} m²".format(wall.Id, area_m2))


if __name__ == "__main__":
    run_script()