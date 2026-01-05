# -*- coding: utf-8 -*-
import sys
import os
import csv
from pyrevit import script, DB

output = script.get_output()
output.print_md("# 📤 BEM LIBRARY EXPORTER")

# Output path (Desktop)
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
csv_path = os.path.join(desktop, "BEM_Library_Export.csv")


def get_safe_name(element):
    """Safely gets the name of a type."""
    if not element: return ""
    p = element.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if p and p.HasValue: return p.AsString()
    return element.Name


def get_r_value(thickness, conductivity):
    """Calculates R = d/k"""
    try:
        if conductivity > 0:
            return thickness / conductivity
    except:
        return 0
    return 0


def run_export():
    doc = __revit__.ActiveUIDocument.Document

    # 1. Collect all System Families
    categories = [DB.WallType, DB.FloorType, DB.RoofType]
    library_data = []

    print("Scanning Template for 'CTE' items...")

    for cat in categories:
        collector = DB.FilteredElementCollector(doc).OfClass(cat)

        for elem in collector:
            # Check for the Tag
            p_tag = elem.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
            if p_tag and p_tag.AsString() == "CTE":

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

                    # Thermal (Try to read asset)
                    k_val = 0
                    if mat:
                        asset_id = mat.ThermalAssetId
                        if asset_id != DB.ElementId.InvalidElementId:
                            asset_elem = doc.GetElement(asset_id)
                            # This is a bit complex in API, simplified here:
                            # We trust the material name carries the intent
                            pass

                    # Row: [Category, Type Name, Layer Index, Material, Thickness(m)]
                    row = [category_name, type_name, i + 1, mat_name, "{:.3f}".format(th_m)]
                    library_data.append(row)

    # 2. Write to CSV
    if library_data:
        try:
            with open(csv_path, 'wb') as f:  # 'wb' for Python 2 (IronPython)
                writer = csv.writer(f)
                # Header
                writer.writerow(["Category", "Assembly Name", "Layer #", "Material Name", "Thickness (m)"])
                # Data
                writer.writerows(library_data)

            print("\n✅ EXPORT SUCCESS!")
            print("File saved to: " + csv_path)
            output.print_md("### [Click here to open folder](file:///{})".format(desktop.replace("\\", "/")))
        except Exception as e:
            print("❌ Error writing file: " + str(e))
    else:
        print("⚠️ No items found with Type Comments = 'CTE'")


if __name__ == "__main__":
    run_export()