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
from bem_utils import logger, FT_TO_M
from Autodesk.Revit.DB import *



def run_material_audit():
    logger.info("--- 🧱 BEM: WALL CONSTRUCTION AUDIT ---")

    walls = FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType()

    for wall in walls:
        wall_type = wall.WallType
        structure = wall_type.GetCompoundStructure()

        if not structure:
            continue

        print("\nStructure for Wall: {}".format(wall_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()))

        # CompoundStructure measures layers from Exterior to Interior
        layers = structure.GetLayers()
        for i, layer in enumerate(layers):
            mat_id = layer.MaterialId
            material = doc.GetElement(mat_id)
            mat_name = material.Name if material else "No Material Assigned"

            # Convert internal feet to Meters
            thickness_m = layer.Width * FT_TO_M

            print("  Layer {}: {} | Thickness: {:.3f}m".format(i, mat_name, thickness_m))


run_material_audit()

# -*- coding: utf-8 -*-
# noinspection PyUnresolvedReferences
from bem_utils import logger, FT_TO_M
from Autodesk.Revit.DB import *

# Standard Boilerplate
# noinspection PyUnreachableCode
if False:
    # noinspection PyUnresolvedReferences
    from Autodesk.Revit.UI import UIApplication

    __revit__ = UIApplication()
    doc = Document()

# noinspection PyUnboundLocalVariable
doc = __revit__.ActiveUIDocument.Document


def get_thermal_conductivity(material):
    """Reaches into the Material's Thermal Asset to get conductivity (k)"""
    asset_id = material.ThermalAssetId
    if asset_id == ElementId.InvalidElementId:
        return None

    asset_elem = doc.GetElement(asset_id)
    # Conductivity in Revit is stored in W/(m·K)
    # Parameter is typically: THERMAL_CONDUCTIVITY
    k_param = asset_elem.get_Parameter(BuiltInParameter.THERMAL_CONDUCTIVITY)
    if k_param:
        return k_param.AsDouble()
    return None


def run_script():
    logger.info("--- 🌡️ BEM: THERMAL ASSET EXTRACTION ---")

    walls = FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType()

    for wall in walls:
        structure = wall.WallType.GetCompoundStructure()
        if not structure: continue

        print("\nWall: {}".format(wall.Id))

        layers = structure.GetLayers()
        for layer in layers:
            material = doc.GetElement(layer.MaterialId)
            if not material: continue

            d = layer.Width * FT_TO_M  # Thickness in meters
            k = get_thermal_conductivity(material)  # Conductivity in W/mK

            if k:
                r_value = d / k
                print("  Layer: {:<15} | k: {:.3f} W/mK | R: {:.3f} m²K/W".format(
                    material.Name[:15], k, r_value))
            else:
                print("  Layer: {:<15} | ⚠️ NO THERMAL ASSET".format(material.Name[:15]))


if __name__ == "__main__":
    run_script()