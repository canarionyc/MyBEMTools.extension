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
# -*- coding: utf-8 -*-
# noinspection PyUnresolvedReferences
from bem_utils import logger
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import *

# IDE MOCKING
# noinspection PyUnreachableCode
if False:
    # noinspection PyUnresolvedReferences
    from Autodesk.Revit.UI import UIApplication

    __revit__ = UIApplication()
    doc = Document()

# RUNTIME ASSIGNMENT
# noinspection PyUnboundLocalVariable
doc = __revit__.ActiveUIDocument.Document


def run_script():
    logger.info("--- LESSON 2.2: BEM PARAMETER TAGGING ---")

    # 1. Collect all Wall instances
    walls = FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType().ToElements()

    # 2. Start a Transaction (Required to modify anything in Revit)
    t = Transaction(doc, "BEM: Tag Basement Walls")
    t.Start()

    try:
        tagged_count = 0
        for wall in walls:
            # Check the Base Level name to identify "Basement"
            base_level_id = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT).AsElementId()
            base_level = doc.GetElement(base_level_id)
            level_name = base_level.Name.lower()

            # Logic: If level contains "basement" or "level -1", tag it
            if "basement" in level_name or "-1" in level_name:
                # We use the 'Comments' parameter as our BEM storage for now
                comment_param = wall.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)

                if comment_param:
                    comment_param.Set("BEM_GROUND_COUPLED")
                    tagged_count += 1

        t.Commit()
        logger.info("SUCCESS: Tagged {} walls for ground-coupling analysis.".format(tagged_count))

    except Exception as e:
        t.RollBack()
        logger.error("FAILED: Transaction rolled back. Error: {}".format(str(e)))


if __name__ == "__main__":
    run_script()