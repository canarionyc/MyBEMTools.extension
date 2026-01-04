# -*- coding: utf-8 -*-
import sys
import unicodedata
from Autodesk.Revit import DB

# --- ENVIRONMENT SETUP ---
if not hasattr(sys.stdout, 'flush'):
    sys.stdout.flush = lambda: None

# --- CONSTANTS ---
db_path = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\hulc_data.sqlite"


# --- HELPER FUNCTIONS ---
def sanitize_revit_name(text):
    if not text: return "Unnamed_Material"
    nfkd_form = unicodedata.normalize('NFKD', str(text))
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    translations = {
        "<": "inf", ">": "sup", "[": "(", "]": ")",
        "{": "(", "}": ")", "|": "-", ";": ",", "?": "",
        ":": "-", "/": "-"
    }
    for char, replacement in translations.items():
        text = text.replace(char, replacement)
    return " ".join(text.split())


def update_material_thermal_data(doc, data):
    # 1. Prepare Names
    raw_name = data['material']
    safe_name = sanitize_revit_name(raw_name)
    asset_name = safe_name + "_Thermal"

    print("    [BEM_ENV] Processing: '{}'".format(safe_name))

    # 2. MANUAL MATH (Safe Calculation)
    try:
        k_imp = float(data['conductivity']) * 0.577789
        d_imp = float(data['density']) * 0.062428
        cp_imp = float(data['specificheat']) * 0.000238846

        # Safety Clamps (Revit crashes on <= 0)
        k_imp = max(0.001, k_imp)
        d_imp = max(0.001, d_imp)
        cp_imp = max(0.001, cp_imp)
    except Exception as e:
        print("    [ERROR] Math calculation failed: {}".format(e))
        return None

    # 3. Find Material
    material = next((m for m in DB.FilteredElementCollector(doc).OfClass(DB.Material)
                     if m.Name == safe_name), None)

    if not material:
        mat_id = DB.Material.Create(doc, safe_name)
        material = doc.GetElement(mat_id)

    # 4. MANAGE ASSET (The Reconstruction Strategy)
    asset_id = material.ThermalAssetId

    try:
        # Create a FRESH object in memory.
        # We do NOT rely on 'pse.GetThermalAsset()' which might be corrupt.
        new_asset = DB.ThermalAsset(asset_name, DB.ThermalMaterialType.Solid)
        new_asset.ThermalConductivity = k_imp
        new_asset.Density = d_imp
        new_asset.SpecificHeat = cp_imp

        if asset_id == DB.ElementId.InvalidElementId:
            # --- SCENARIO A: NO ASSET LINKED ---
            # Check for Orphans (Naming Collision Prevention)
            collector = DB.FilteredElementCollector(doc).OfClass(DB.PropertySetElement)
            orphan = next((e for e in collector if e.Name == asset_name), None)

            if orphan:
                print("    [BEM_ENV] Found Orphan. Overwriting...")
                # Inject the FRESH asset into the ORPHAN element
                orphan.SetThermalAsset(new_asset)
                material.ThermalAssetId = orphan.Id
            else:
                # Create Brand New Element
                print("    [BEM_ENV] Creating New Asset...")
                pse_id = DB.PropertySetElement.Create(doc, new_asset)
                material.ThermalAssetId = pse_id

        else:
            # --- SCENARIO B: ASSET ALREADY LINKED ---
            # Force Overwrite: We ignore whatever data was there and inject the new object.
            pse = doc.GetElement(asset_id)

            # Verify name consistency (Optional, keeps DB clean)
            if pse.Name != asset_name:
                try:
                    pse.Name = asset_name
                except:
                    pass  # Ignore naming errors if locked

            pse.SetThermalAsset(new_asset)
            print("    [BEM_ENV] Asset Overwritten (Refreshed).")

    except Exception as e:
        # If this fails, the element is truly broken (Internal Error).
        # Last Resort: Delete and Recreate (Uncomment if still failing)
        print("    [BEM_ENV_ERROR] Hard Refresh Failed: {}".format(e))
        return material.Id

    return material.Id