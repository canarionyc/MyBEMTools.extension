# -*- coding: utf-8 -*-
import os
import sys


# Define a robust logger that forces output to the console immediately
def log(msg, error=False):
    stream = sys.stderr if error else sys.stdout
    stream.write("--- [BEM LOG]: {} ---\n".format(msg))
    stream.flush()


log("PROCESS STARTED")

# 1. Setup paths
try:
    current_dir = os.path.dirname(__file__)
    lib_path = os.path.abspath(os.path.join(current_dir, "../../../lib"))
    if lib_path not in sys.path:
        sys.path.append(lib_path)
    log("Paths initialized. Lib at: {}".format(lib_path))
except Exception as e:
    log("Path Setup Error: {}".format(e), True)

# 2. Imports
try:
    from Autodesk.Revit.DB import *
    from pyrevit import revit, script

    log("Revit API and pyRevit modules loaded.")
except Exception as e:
    log("Import Error (API/pyRevit): {}".format(e), True)
    sys.exit(1)

# 3. Document Acquisition
doc = None
try:
    if '__models__' in globals() and __models__:
        model_path = __models__[0]  # This is a STRING
        log("Opening model: {}".format(model_path))
        # You MUST open the document yourself in headless mode
        doc = revit.app.OpenDocumentFile(model_path)

    if not doc:
        doc = revit.doc  # Fallback for UI mode

    if doc:
        log("Successfully linked to: {}".format(doc.Title))
    else:
        log("FATAL: No document could be acquired.", True)
        sys.exit(1)
except Exception as e:
    log("Initialization Error: {}".format(e), True)
    sys.exit(1)
    
if not doc:
    log("FATAL: No document found after all attempts.", True)
    sys.exit(1)

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


# --- THERMAL CATALOG (Mapped from JSON) ---
# Equivalent materials for 0.50m thickness in Revit
thermal_catalog = {
    "BEM_ROOF": {
        "u_value": 0.170,
        "conductivity": 0.085,
        "density": 260,
        "specific_heat": 1000,
        "note": "Cubierta en Teja"
    },
    "BEM_WALL": {
        "u_value": 0.220,
        "conductivity": 0.110,
        "density": 760,
        "specific_heat": 1000,
        "note": "Muro Exterior 0.60 Equivalent"
    },
    "BEM_FLOOR": {
        "u_value": 0.480,
        "conductivity": 0.240,
        "density": 690,
        "specific_heat": 1050,
        "note": "Solera/Sanitario Equivalent"
    }
}

# --- MODEL HIERARCHY ---
model_hierarchy = [
    {
        "level": "BEM_P01_BASE",
        "elevation": -1.00,
        "rooms": [BEMRoom("2147499056", "P01_E01_CAMARA")],
        "elements": [
            BEMElement("2147499031", "BEM_Wall_500mm", 0.500, thermal_catalog["BEM_WALL"]),
            BEMElement("2147499037", "BEM_Floor_500mm", 0.500, thermal_catalog["BEM_FLOOR"])
        ]
    },
    {
        "level": "BEM_P02_GROUND",
        "elevation": 0.00,
        "rooms": [BEMRoom("2147499086", "P02_E01_LIVING")],
        "elements": [
            BEMElement("2147499044", "BEM_Floor_500mm", 0.500, thermal_catalog["BEM_FLOOR"])
        ]
    },
    {
        "level": "BEM_P04_EAVE",
        "elevation": 4.50,
        "rooms": [],
        "elements": [
            BEMElement("2147499411", "BEM_Roof_500mm", 0.500, thermal_catalog["BEM_ROOF"])
        ]
    }
]


def print_audit_tree():
    log("GENERATING REPORT")
    print("\n" + "="*40)
    print(" BEM AUDIT TREE: " + doc.Title)
    print("="*40)
    # ... your reporting logic ...
    log("REPORT FINISHED")

# --- EXECUTION ---
try:
    print_audit_tree()
except Exception as e:
    log("Audit Execution Error: {}".format(e), True)

log("PROCESS COMPLETE")
