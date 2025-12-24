import sys
import os
from pyrevit import revit, DB, HOST_APP

# Check engine version programmatically
import sys
if sys.version_info.major < 3:
    raise RuntimeError("BEM Audit Tool requires IronPython 3+. Current: " + sys.version)

# This will cause a SyntaxError on IronPython 2.7, failing the script immediately
print(f"Running on Engine: {HOST_APP.engine_type}")
print(f"Arguments: {sys.argv}")

# Replace line 6 with:
print("Host Version: {}".format(HOST_APP.version))
print("Running in UI mode: {}".format(HOST_APP.is_ui))
print("Python Version: {}".format(sys.version))
print("Arguments received: {}".format(sys.argv))


def find_model_path():
    """Tries multiple sources to find the model path in headless mode."""
    # 1. Try sys.argv (standard for CLI tools)
    rvt_args = [arg for arg in sys.argv if arg.lower().endswith('.rvt')]
    if rvt_args:
        return rvt_args[0]

    # 2. Try JournalData (source of truth in the runner journal)
    try:
        j_data = HOST_APP.app.JournalData
        if j_data and j_data.ContainsKey("Models"):
            return j_data["Models"].split(';')[0]
    except:
        pass

    # 3. Fallback to pyRevit global
    models = globals().get('__models__', [])
    if models:
        return models[0]

    return None


# --- Main Document Logic ---
doc = None
path = find_model_path()

if path:
    print("Headless Mode: Opening model at {}".format(path))
    if os.path.exists(path):
        try:
            # Must use Application.OpenDocumentFile in UI-less mode
            doc = HOST_APP.app.OpenDocumentFile(path)
        except Exception as e:
            print("CRITICAL: Failed to open model via API. Error: {}".format(e))
    else:
        print("ERROR: File not found at path: {}".format(path))
else:
    # UI Mode Fallback (for testing within Revit UI)
    try:
        doc = revit.doc
    except:
        pass

if not doc:
    print("ERROR: No valid Revit Document found.")
    sys.exit(1)

print("SUCCESS: Attached to document '{}'".format(doc.Title))


# ... Rest of your BEM audit code ...

# ... Rest of your script follows ...

# ... proceed with your BEM audit logic ...
# Now 'doc' is a valid Autodesk.Revit.DB.Document object for both modes.
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