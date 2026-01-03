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

# -*- coding: utf-8 -*-
from bem_utils import logger, FT_TO_M, R_SI, R_SE
from Autodesk.Revit.DB import *

# Standard Header
# noinspection PyUnreachableCode
if False:
    from Autodesk.Revit.UI import UIApplication

    __revit__ = UIApplication()
    doc = Document()

doc = __revit__.ActiveUIDocument.Document


def get_k(material):
    """Utility to safely get conductivity"""
    asset_id = material.ThermalAssetId
    if asset_id == ElementId.InvalidElementId:
        return None
    asset = doc.GetElement(asset_id)
    k_param = asset.get_Parameter(BuiltInParameter.THERMAL_CONDUCTIVITY)
    return k_param.AsDouble() if k_param else None


def run_thermal_audit():
    logger.info("--- 🌡️ LESSON 3.1: ASSEMBLY U-VALUE ANALYSIS ---")

    walls = FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType()

    for wall in walls:
        wall_type = wall.WallType
        structure = wall_type.GetCompoundStructure()
        if not structure: continue

        # Start with Surface Resistances
        total_r = R_SI + R_SE
        valid_data = True

        print("\nAnalyzing: {}".format(wall_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()))

        layers = structure.GetLayers()
        for layer in layers:
            material = doc.GetElement(layer.MaterialId)
            d = layer.Width * FT_TO_M  # Thickness in meters
            k = get_k(material) if material else None

            if k and k > 0:
                layer_r = d / k
                total_r += layer_r
                print("  - Layer: {:<15} | R: {:.3f}".format(material.Name[:15], layer_r))
            else:
                # If a layer is missing data, the whole U-Value is a guess
                print("  - Layer: {:<15} | ❌ MISSING THERMAL DATA".format(
                    material.Name[:15] if material else "Unknown"))
                valid_data = False

        # Calculate U = 1 / R_total
        if valid_data:
            u_value = 1.0 / total_r
            print("  >>> TOTAL R-VALUE: {:.3f} m²K/W".format(total_r))
            print("  >>> FINAL U-VALUE: {:.3f} W/(m²K)".format(u_value))

            # BEM Check: Passive House standard is usually < 0.15
            if u_value > 0.30:
                logger.warning("High heat loss detected in this assembly.")
        else:
            logger.error("Could not calculate U-Value due to missing Material Assets.")


run_thermal_audit()