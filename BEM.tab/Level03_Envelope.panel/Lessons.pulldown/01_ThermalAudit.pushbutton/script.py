# -*- coding: utf-8 -*-
from bem_utils import logger, get_readable_units
from Autodesk.Revit.DB import *

doc = __revit__.ActiveUIDocument.Document

logger.info("--- BEM LESSON 3.1 START ---")
logger.debug("Active Project: {}".format(doc.Title))

units = get_readable_units(doc)
logger.info("Current Units: {}".format(units))

# Logic for Lesson 3.1...
