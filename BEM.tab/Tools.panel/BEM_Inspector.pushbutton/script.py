# -*- coding: utf-8 -*-
import sys
from pyrevit import script, DB, revit

output = script.get_output()
output.print_md("# 🕵️ BEM INSPECTOR")


def get_type_layers(doc, element_type):
    """Safely extracts layer info."""
    info = []
    try:
        struct = element_type.GetCompoundStructure()
        if not struct:
            return ["   [No Structure / Simple Layer]"]

        layers = struct.GetLayers()
        for i, l in enumerate(layers):
            mat_id = l.MaterialId
            mat = doc.GetElement(mat_id)
            mat_name = mat.Name if mat else "<No Material>"
            thickness = DB.UnitUtils.ConvertFromInternalUnits(l.Width, DB.UnitTypeId.Meters)
            func = str(l.Function)
            info.append("   Layer {}: {} | {:.3f}m | {}".format(i, mat_name, thickness, func))

    except Exception as e:
        info.append("   [Error reading layers: {}]".format(e))
    return info


def inspect_category(doc, category_class, category_name):
    print("\n" + "=" * 50)
    print("INSPECTING: {}...".format(category_name))

    # 1. Collect
    collector = DB.FilteredElementCollector(doc).OfClass(category_class)
    elements = list(collector)  # Convert to list immediately
    print("Found {} types.".format(len(elements)))

    # 2. Iterate and Print Names
    for i, e in enumerate(elements):
        try:
            # We try multiple ways to get the name to see which one works/fails
            try:
                # Method A: Property
                name_prop = e.Name
            except:
                name_prop = "<Error on .Name>"

            try:
                # Method B: Parameter
                p = e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
                name_param = p.AsString() if p else "<No Param>"
            except:
                name_param = "<Error on Param>"

            # Print the Name
            print("[{}] ID: {} | Name: '{}'".format(i, e.Id, name_prop))

            # 3. Detailed Dump for First 3
            if i < 3:
                print("   --- DETAILS ---")
                layers = get_type_layers(doc, e)
                for line in layers:
                    print(line)
                print("   ---------------")

        except Exception as crash:
            print("❌ CRASH on Index {}: {}".format(i, crash))


def run_inspection():
    doc = __revit__.ActiveUIDocument.Document

    # Inspect Floors
    inspect_category(doc, DB.FloorType, "FLOORS")

    # Inspect Walls
    inspect_category(doc, DB.WallType, "WALLS")

    # Inspect Roofs
    inspect_category(doc, DB.RoofType, "ROOFS")

    print("\n✅ Inspection Finished")


if __name__ == "__main__":
    run_inspection()