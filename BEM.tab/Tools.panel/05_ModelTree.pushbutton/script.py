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


# 05_ModelTree/script.py
# Project: EJEMPLO1-2526_20251222
# BEM Audit Script - IronPython 2.7 Compatible Version

class BEMElement:
    def __init__(self, element_id, element_type, thickness=0.0, thermal_data=None):
        self.element_id = element_id
        self.element_type = element_type
        self.thickness = thickness
        self.thermal_data = thermal_data or "PENDING"


class BEMRoom:
    def __init__(self, room_id, name, status="PLACED"):
        self.room_id = room_id
        self.name = name
        self.status = status


# --- THERMAL CATALOG (Digital Twin Properties) ---
thermal_catalog = {
    "BEM_ROOF_U_017_k_0085": {
        "u_value": 0.170,  # W/m2K
        "conductivity": 0.085,  # W/mK
        "density": 260,  # kg/m3
        "specific_heat": 1000,  # J/kgK
        "composition": "Equivalent: Clay tile, XPS, EPS Forjado, Plaster"
    },
    "BEM_WALL_500MM": "PENDING",
    "BEM_FLOOR_500MM": "PENDING"
}

# --- MODEL HIERARCHY DATA ---
model_hierarchy = [
    {
        "level": "BEM_P01_BASE",
        "elevation": -1.00,
        "rooms": [BEMRoom("2147499056", "P01_E01_CAMARA")],
        "elements": [
            BEMElement("2147499031", "BEM_Wall_500mm", 0.500),
            BEMElement("2147499032", "BEM_Wall_500mm", 0.500),
            BEMElement("2147499033", "BEM_Wall_500mm", 0.500),
            BEMElement("2147499034", "BEM_Wall_500mm", 0.500),
            BEMElement("2147499037", "BEM_Floor_500mm", 0.500)
        ]
    },
    {
        "level": "BEM_P02_GROUND",
        "elevation": 0.00,
        "rooms": [BEMRoom("2147499086", "P02_E01_LIVING")],
        "elements": [
            BEMElement("2147499044", "BEM_Floor_500mm", 0.500)
        ]
    },
    {
        "level": "BEM_P03_ATTIC",
        "elevation": 4.00,
        "rooms": [],
        "elements": [
            BEMElement("2147499051", "BEM_Floor_500mm", 0.500)
        ]
    },
    {
        "level": "BEM_P04_EAVE",
        "elevation": 4.50,
        "rooms": [],
        "elements": [
            BEMElement(
                "2147499411",
                "BEM_Roof_500mm",
                0.500,
                thermal_data=thermal_catalog["BEM_ROOF_U_017_k_0085"]
            )
        ]
    }
]


def print_audit_tree():
    print("PROJECT: EJEMPLO1-2526_20251222")
    print("BEM AUDIT TREE REPORT")
    print("-" * 60)

    for data in model_hierarchy:
        # Replaced f-string with .format() for IronPython 2.7 compatibility
        print("\nLEVEL: {0} (Elev: {1}m)".format(data['level'], data['elevation']))

        if not data["rooms"]:
            print("|-- STATUS: No Rooms/Zones defined.")
        for room in data["rooms"]:
            print("|-- ROOM: {0} (ID: {1}) [{2}]".format(room.name, room.room_id, room.status))

        for el in data["elements"]:
            print("|-- {0} (ID: {1})".format(el.element_type, el.element_id))
            print("    |-- Thickness: {0}m".format(el.thickness))

            if isinstance(el.thermal_data, dict):
                thermal = el.thermal_data
                print("    |-- Thermal: U={0} | k={1}".format(thermal['u_value'], thermal['conductivity']))
            else:
                print("    |-- Thermal: {0}".format(el.thermal_data))


if __name__ == "__main__":
    print_audit_tree()