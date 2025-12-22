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

# -*- coding: utf-8 -*-
import csv
import os
from datetime import datetime
# noinspection PyUnresolvedReferences
from bem_utils import logger, FT_TO_M, SQFT_TO_M2, R_SI, R_SE
from Autodesk.Revit.DB import *


def get_k(material):
    asset_id = material.ThermalAssetId
    if asset_id == ElementId.InvalidElementId: return None
    asset = doc.GetElement(asset_id)
    k_param = asset.get_Parameter(BuiltInParameter.THERMAL_CONDUCTIVITY)
    return k_param.AsDouble() if k_param else None


def calculate_u(wall):
    structure = wall.WallType.GetCompoundStructure()
    if not structure: return "N/A"

    total_r = R_SI + R_SE
    for layer in structure.GetLayers():
        mat = doc.GetElement(layer.MaterialId)
        k = get_k(mat) if mat else None
        if k and k > 0:
            total_r += (layer.Width * FT_TO_M) / k
        else:
            return "MISSING_DATA"
    return round(1.0 / total_r, 4)


def run_export():
    # 1. Define File Path (Save to Desktop)
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = "BEM_Export_{}.csv".format(timestamp)
    filepath = os.path.join(desktop, filename)

    logger.info("Starting BEM Export to: {}".format(filename))

    walls = FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType()

    # 2. Open CSV for writing
    with open(filepath, 'wb') as f:  # Use 'wb' for IronPython 2.7 compatibility
        writer = csv.writer(f)
        # Header Row
        writer.writerow(["Wall_ID", "Type_Name", "Area_m2", "U_Value_W_m2K", "UA_Product", "Comments"])

        for wall in walls:
            area_m2 = wall.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED).AsDouble() * SQFT_TO_M2
            u_val = calculate_u(wall)

            # Calculate UA (Total heat loss per degree of temp difference)
            ua_product = "N/A"
            if isinstance(u_val, float):
                ua_product = round(u_val * area_m2, 4)

            comments = wall.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).AsString() or ""

            writer.writerow([
                wall.Id.IntegerValue,
                wall.WallType.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(),
                round(area_m2, 2),
                u_val,
                ua_product,
                comments
            ])

    logger.info("✅ SUCCESS: Exported to Desktop.")
    os.startfile(desktop)  # Automatically opens the folder so you can see your file


run_export()