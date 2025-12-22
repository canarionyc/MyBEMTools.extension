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
# noinspection PyUnresolvedReferences
from bem_utils import logger, CUFT_TO_M3
from Autodesk.Revit.DB import *
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import VolumeComputationSetting

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Architecture import Room


def run_script():
    # 1. Access the setting via doc.Settings
    current_setting = doc.Settings.VolumeComputationSetting

    if current_setting == VolumeComputationSetting.NotCalculated:
        logger.warning("Volume calculations were OFF. Enabling them now for BEM...")

        # 2. You must use a Transaction to change this setting!
        t = Transaction(doc, "Enable Volume Calc")
        t.Start()
        doc.Settings.VolumeComputationSetting = VolumeComputationSetting.Calculated
        t.Commit()

        logger.info("Volume calculations are now ENABLED.")
    else:
        logger.info("Volume calculations are already active.")

    rooms = FilteredElementCollector(doc).OfClass(SpatialElement).ToElements()

    for room in rooms:
        if isinstance(room, Room) and room.Area > 0:
            # Internal (cubic feet) -> m³
            vol_m3 = room.Volume * CUFT_TO_M3
            logger.info("Zone: {} | Volume: {:.2f} m³".format(room.Name, vol_m3))


run_script()