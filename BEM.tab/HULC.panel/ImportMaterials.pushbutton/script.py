# -*- coding: utf-8 -*-
"""
Import HULC Materials (Nuclear Option)
1. Auto-detects encoding (UTF-8 vs Windows-1252) to fix "métrico" errors.
2. Silences "Duplicate Mark" warnings automatically.
3. Sets full Thermal Assets.
"""
import sys
import os
import re
import json
import io
import clr

# --- REVIT API SETUP ---
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog

# --- CONFIGURATION ---
JSON_PATH = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\materials.json"


# ============================================================================
# 1. WARNING SWALLOWER (Fixes "Duplicate Mark" spam)
# ============================================================================
class WarningSwallower(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        # Get all warnings
        failures = failuresAccessor.GetFailureMessages()
        for f in failures:
            # Check if it's a "Duplicate Value" warning (standard for Marks)
            # We treat it as a Warning, not an Error, so we can just delete it.
            id = f.GetFailureDefinitionId()
            if BuiltInFailures.GeneralFailures.DuplicateValue == id:
                failuresAccessor.DeleteWarning(f)
        return FailureProcessingResult.Continue


# ============================================================================
# 2. ROBUST DECODING (Fixes "unknown codec 0xe9")
# ============================================================================
def safe_decode(text):
    """
    Tries to convert text to Unicode.
    1. If it's already unicode, return it.
    2. Try UTF-8.
    3. If that fails (byte 0xE9), try CP1252 (Windows Standard).
    """
    if not text: return u""
    if isinstance(text, unicode): return text

    # It's a bytestring, let's try to decode it
    try:
        return text.decode('utf-8')
    except UnicodeDecodeError:
        try:
            # 0xE9 implies Windows-1252 (Western European)
            return text.decode('cp1252')
        except:
            # Last resort: ignore garbage
            return text.decode('utf-8', 'ignore')


# ============================================================================
# 3. HELPER FUNCTIONS
# ============================================================================
def alert(title, msg):
    try:
        TaskDialog.Show(title, msg)
    except:
        # Fallback if msg has weird chars
        TaskDialog.Show(title, "Script Finished (Message contains complex chars)")


def to_internal(value, unit_type):
    # SI -> Imperial conversion
    if unit_type == "density":
        return value * 0.06242796  # kg/m3 -> lb/ft3
    elif unit_type == "conductivity":
        return value * 0.577789  # W/mK -> BTU/h-ft-F
    elif unit_type == "specific_heat":
        return value * 0.0002388459  # J/kgK -> BTU/lb-F
    return value


def clean_name(text):
    # Ensure it's unicode first
    text = safe_decode(text)

    # Remove Revit-illegal chars
    forbidden = {
        u"<": u"inf", u">": u"sup",
        u"[": u"(", u"]": u")",
        u"{": u"(", u"}": u")",
        u"|": u"-", u"\\": u"-", u"/": u"-",
        u":": u"-", u";": u",",
        u"*": u"x", u"?": u""
    }
    for char, rep in forbidden.items():
        text = text.replace(char, rep)

    return u" ".join(text.split())


def process_hulc_name(raw_name):
    s = safe_decode(raw_name)
    # Regex for "100 < d < 200"
    pattern = r"(\d+(?:\.\d+)?)\s*<\s*d\s*<\s*(\d+(?:\.\d+)?)"
    replacement = r"d entre \1 y \2"
    clean = re.sub(pattern, replacement, s)
    return clean_name(clean)


def set_thermal_properties(doc, material, k, d, cp):
    # Use IDs to avoid "AttributeError"
    # THERMAL_MATERIAL_CONDUCTIVITY = -1001301
    # THERMAL_MATERIAL_DENSITY = -1001300
    # THERMAL_MATERIAL_SPECIFIC_HEAT = -1001302

    therm_asset_id = material.ThermalAssetId

    if therm_asset_id == ElementId.InvalidElementId:
        try:
            pse = PropertySetElement.Create(doc, MaterialAspect.Thermal, u"Thermal_" + material.Name)
            material.ThermalAssetId = pse.Id
            therm_asset = pse
        except:
            return False
    else:
        therm_asset = doc.GetElement(therm_asset_id)

    if not therm_asset: return False

    p_cond = therm_asset.get_Parameter(BuiltInParameter(-1001301))
    if p_cond: p_cond.Set(to_internal(float(k), "conductivity"))

    p_dens = therm_asset.get_Parameter(BuiltInParameter(-1001300))
    if p_dens: p_dens.Set(to_internal(float(d), "density"))

    p_cp = therm_asset.get_Parameter(BuiltInParameter(-1001302))
    if p_cp: p_cp.Set(to_internal(float(cp), "specific_heat"))

    return True


# ============================================================================
# 4. MAIN EXECUTION
# ============================================================================
def run():
    doc = __revit__.ActiveUIDocument.Document

    if not os.path.exists(JSON_PATH):
        alert("Error", "File not found: " + JSON_PATH)
        return

    # 1. READ JSON (Hybrid approach)
    # We read as binary, then decode the JSON string manually to handle mixed encodings
    try:
        with open(JSON_PATH, 'rb') as f:
            raw_bytes = f.read()

        # Try UTF-8 first
        try:
            json_str = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to Windows-1252
            json_str = raw_bytes.decode('cp1252')

        data = json.loads(json_str)

    except Exception as e:
        alert("Read Error", "Could not parse JSON.\n" + str(e))
        return

    # 2. TRANSACTION WITH SWALLOWER
    t = Transaction(doc, "Import HULC Materials")

    # Setup Warning Swallower
    options = t.GetFailureHandlingOptions()
    swallower = WarningSwallower()
    options.SetFailuresPreprocessor(swallower)
    t.SetFailureHandlingOptions(options)

    t.Start()

    count = 0
    errors = []
    material_cache = {}

    for item in data:
        # We assume 'item' dict keys/values are now proper unicode
        raw_name = item.get('name', 'Unnamed')

        try:
            # Process Name
            final_name = process_hulc_name(raw_name)

            # Find/Create
            mat = None
            if final_name.lower() in material_cache:
                mat = material_cache[final_name.lower()]
            else:
                col = FilteredElementCollector(doc).OfClass(Material)
                for m in col:
                    if m.Name == final_name:
                        mat = m
                        break
                if not mat:
                    try:
                        new_id = Material.Create(doc, final_name)
                        mat = doc.GetElement(new_id)
                    except:
                        # Collision fallback
                        final_name = final_name + u"_Imp"
                        new_id = Material.Create(doc, final_name)
                        mat = doc.GetElement(new_id)

                if mat: material_cache[final_name.lower()] = mat

            # Properties
            if mat:
                # Identity Data
                mat_group = item.get('material_group', 'General')
                k = item.get('conductivity', 0.0)
                d = item.get('density', 0.0)
                cp = item.get('specificheat', 0.0)

                # Set Identity Parameters (IDs)
                p_class = mat.get_Parameter(BuiltInParameter(-1002101))
                if p_class: p_class.Set(safe_decode(mat_group))

                p_desc = mat.get_Parameter(BuiltInParameter(-1001202))
                if p_desc: p_desc.Set(u"Density: {} kg/m3".format(d))

                p_model = mat.get_Parameter(BuiltInParameter(-1001203))
                if p_model: p_model.Set(str(k))

                # Set Thermal Asset
                if k > 0:
                    set_thermal_properties(doc, mat, k, d, cp)

                count += 1

        except Exception as e:
            # Handle error reporting gracefully
            err_msg = u"{} -> {}".format(raw_name, str(e))
            errors.append(err_msg)

    t.Commit()

    # Report
    msg = u"Success: {}\nErrors: {}".format(count, len(errors))
    if errors:
        msg += u"\n\nFirst 3 Errors:\n" + u"\n".join(errors[:3])

    alert("Import Complete", msg)


try:
    run()
except Exception as e:
    alert("Critical Fail", str(e))