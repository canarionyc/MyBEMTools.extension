# -*- coding: utf-8 -*-
import sys
import os
import csv
from pyrevit import script, DB

output = script.get_output()
output.print_md("# 📤 BEM LIBRARY EXPORTER")

# Output path (Desktop)
desktop = os.path.join(os.path.expanduser("~"), "OneDrive - Universidad de La Laguna", "Desktop")
if not os.path.exists(desktop):
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")

csv_path = os.path.join(desktop, "BEM_Library_Export.csv")

def get_safe_name(element):
    """Safely gets the name of a type."""
    if not element: return "Unknown"
    p = element.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if p and p.HasValue: return p.AsString()
    return element.Name

def run_export():
    doc = __revit__.ActiveUIDocument.Document

    # 1. Collect all System Families
    categories = [DB.WallType, DB.FloorType, DB.RoofType]
    library_data = []

    print("Scanning model for Family Types...")

    for cat in categories:
        collector = DB.FilteredElementCollector(doc).OfClass(cat)

        for elem in collector:
            type_name = get_safe_name(elem)
            category_name = elem.Category.Name

            # Analyze Structure
            struct = elem.GetCompoundStructure()
            if not struct: continue

            layers = struct.GetLayers()

            # Extract Layer Data
            for i, layer in enumerate(layers):
                mat_id = layer.MaterialId
                mat = doc.GetElement(mat_id)
                mat_name = mat.Name if mat else "No Material"

                # Geometry
                th_rvt = layer.Width
                th_m = DB.UnitUtils.ConvertFromInternalUnits(th_rvt, DB.UnitTypeId.Meters)

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

                # Format data safely for CSV
                k_str = "{:.3f}".format(k_val) if k_val > 0 else "-"
                r_str = "{:.3f}".format(r_val) if r_val > 0 else "-"
                th_str = "{:.3f}".format(th_m)

                # Row: [Category, Type Name, Layer Index, Material, Thickness, Conductivity, R-Value]
                row = [category_name, type_name, str(i + 1), mat_name, th_str, k_str, r_str]
                library_data.append(row)

    # 2. Write to CSV with UTF-8 Encoding
    if library_data:
        try:
            with open(csv_path, 'wb') as f:
                f.write('\xef\xbb\xbf')  # <--- THIS IS THE MAGIC BOM LINE
                writer = csv.writer(f)
                # Header
                header = ["Category", "Assembly Name", "Layer #", "Material Name", "Thickness (m)", "Conductivity (W/mK)", "R-Value"]
                writer.writerow(header)
                
                # Data - Force UTF-8 encoding on every item to bypass ASCII crashes
                for row in library_data:
                    encoded_row = [unicode(item).encode('utf-8') for item in row]
                    writer.writerow(encoded_row)

            print("\n✅ EXPORT SUCCESS!")
            print("File saved to: " + csv_path)
            output.print_md("### [Click here to open folder](file:///{})".format(desktop.replace("\\", "/")))
        except Exception as e:
            print("❌ Error writing file: " + str(e))
    else:
        print("⚠️ No items found.")

if __name__ == "__main__":
    run_export()