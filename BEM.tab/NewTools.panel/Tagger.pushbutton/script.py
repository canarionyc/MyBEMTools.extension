# -*- coding: utf-8 -*-
from pyrevit import script, DB, revit

output = script.get_output()
output.print_md("# 🏷️ BEM TAGGER: Force Update")

# The exact list of assemblies we created
TARGET_NAMES = [
    "FOR INT",
    "FOR INT AC-NH",
    "MURO CAM SANIT",
    "MURO EXTERIOR",
    "SOL CAM SANIT",
    "TAB INT",
    "FOR CAM SANIT",
    "CUB IN TEJA"
]


def get_safe_name(element):
    """Safely gets the name of a type."""
    if not element: return ""
    p = element.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if p and p.HasValue: return p.AsString().upper()
    return element.Name.upper()


def run_tagger():
    doc = __revit__.ActiveUIDocument.Document
    t = DB.Transaction(doc, "BEM: Force Tags")
    t.Start()

    found_count = 0

    # scan Walls, Floors, Roofs
    categories = [DB.WallType, DB.FloorType, DB.RoofType]

    for cat in categories:
        collector = DB.FilteredElementCollector(doc).OfClass(cat)
        for elem in collector:
            e_name = get_safe_name(elem)

            # If this element is in our target list
            if e_name in TARGET_NAMES:
                try:
                    # Try setting TYPE COMMENTS
                    p = elem.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
                    if p:
                        p.Set("CTE")
                        print("✅ Tagged: {}".format(e_name))
                        found_count += 1
                except Exception as e:
                    print("❌ Failed: {} | {}".format(e_name, e))

    t.Commit()
    print("\nDONE. Tagged {} elements.".format(found_count))


if __name__ == "__main__":
    run_tagger()