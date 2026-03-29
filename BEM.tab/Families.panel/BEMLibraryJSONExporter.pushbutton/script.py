# -*- coding: utf-8 -*-
import sys
import os
import json
from pyrevit import script, DB

output = script.get_output()
output.print_md("# 📤 BEM CATALOG EXPORTER (JSON)")

# Output path (Desktop)
desktop = os.path.join(os.path.expanduser("~"), "OneDrive - Universidad de La Laguna", "Desktop")
if not os.path.exists(desktop):
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")

json_path = os.path.join(desktop, "catalog.json")

def get_safe_name(element):
    """Safely gets the name of a type (Exactly as it was in the CSV script)."""
    if not element: return "Unknown"
    p = element.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if p and p.HasValue: return p.AsString()
    return element.Name

def run_export():
    doc = __revit__.ActiveUIDocument.Document

    # 1. Collect all System Families
    categories = [DB.WallType, DB.FloorType, DB.RoofType]
    
    # NEW: A dictionary to hold the JSON data instead of a list of rows
    catalog = {}

    print("Scanning model for Family Types...")

    for cat in categories:
        collector = DB.FilteredElementCollector(doc).OfClass(cat)

        for elem in collector:
            type_name = get_safe_name(elem)
            category_name = elem.Category.Name

            # Initialize category if missing
            if category_name not in catalog:
                catalog[category_name] = {}
                
            # Initialize assembly if missing
            if type_name not in catalog[category_name]:
                catalog[category_name][type_name] = {
                    "total_thickness_m": 0.0,
                    "layers": []
                }

            # Analyze Structure
            struct = elem.GetCompoundStructure()
            if not struct: continue

            layers = struct.GetLayers()
            total_th_m = 0.0

            # Extract Layer Data (Exactly as it was in the CSV script)
            for i, layer in enumerate(layers):
                mat_id = layer.MaterialId
                mat = doc.GetElement(mat_id)
                mat_name = mat.Name if mat else "No Material"

                # Geometry
                th_rvt = layer.Width
                th_m = DB.UnitUtils.ConvertFromInternalUnits(th_rvt, DB.UnitTypeId.Meters)
                total_th_m += th_m

                # Thermal Extraction
                k_val = 0.0
                r_val = 0.0
                if mat:
                    asset_id = mat.ThermalAssetId
                    if asset_id != DB.ElementId.InvalidElementId:
                        asset_elem = doc.GetElement(asset_id)
                        if asset_elem:
                            try:
                                thermal_asset = asset_elem.GetThermalAsset()
                                k_val = thermal_asset.ThermalConductivity
                                if k_val > 0:
                                    r_val = th_m / k_val
                            except:
                                pass # Skip if the material has no thermal data

                # Append layer data to our JSON dictionary
                catalog[category_name][type_name]["layers"].append({
                    "layer_index": i + 1,
                    "material": mat_name,
                    "thickness_m": round(th_m, 3),
                    "conductivity": round(k_val, 3) if k_val > 0 else None,
                    "r_value": round(r_val, 3) if r_val > 0 else None
                })
            
            # Save total thickness
            catalog[category_name][type_name]["total_thickness_m"] = round(total_th_m, 3)

    # 2. Write to JSON with the EXACT SAME UTF-8 Encoding as your CSV script
    if catalog:
        try:
            # Convert dict to a formatted JSON string
            json_string = json.dumps(catalog, indent=4, ensure_ascii=False)
            
            # Open in binary write mode ('wb') exactly like the CSV script
            with open(json_path, 'wb') as f:
                f.write('\xef\xbb\xbf')  # <--- THE MAGIC BOM LINE
                # Encode the entire JSON string to utf-8 just like the CSV rows
                f.write(unicode(json_string).encode('utf-8'))

            print("\n✅ EXPORT SUCCESS!")
            print("File saved to: " + json_path)
            output.print_md("### [Click here to open folder](file:///{})".format(desktop.replace("\\", "/")))
        except Exception as e:
            print("❌ Error writing file: " + str(e))
    else:
        print("⚠️ No items found.")

if __name__ == "__main__":
    run_export()