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
import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *

doc = __revit__.ActiveUIDocument.Document


def build_final_model():
    print("--- 🏗️ BEM FINAL: HULC COMPLIANT v5.1 ---")

    t = Transaction(doc, "BEM: Final Rebuild")
    t.Start()

    try:
        # 1. DELETE EXISTING GEOMETRY & LEVELS
        print("LOG: Cleaning project for HULC export...")
        for cat in [BuiltInCategory.OST_Walls, BuiltInCategory.OST_Floors,
                    BuiltInCategory.OST_Roofs, BuiltInCategory.OST_Levels]:
            elements = FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType().ToElements()
            for e in elements:
                try:
                    doc.Delete(e.Id)
                except:
                    pass

        # 2. CREATE HULC LEVELS
        print("LOG: Creating HULC Anchors...")
        heights = {
            "BEM_P01_BASE": -1.0 / 0.3048,  # Top of Solera
            "BEM_P02_GROUND": 0.0,  # Top of Living Floor (0.0 datum)
            "BEM_P03_ATTIC": 4.0 / 0.3048,  # Top of Attic Floor
            "BEM_P04_EAVE": 4.5 / 0.3048  # Top of Knee Wall
        }
        lvls = {}
        for name, elev in heights.items():
            l = Level.Create(doc, elev)
            l.Name = name
            lvls[name] = l

        # 3. CREATE 500mm CUSTOM TYPES
        print("LOG: Generating 500mm BEM Materials...")
        # Custom Wall
        w_temp = next(t for t in FilteredElementCollector(doc).OfClass(WallType) if t.Kind == WallKind.Basic)
        bem_wall = w_temp.Duplicate("BEM_Wall_500mm")
        cs_w = bem_wall.GetCompoundStructure()
        cs_w.SetLayerWidth(0, 0.5 / 0.3048)
        bem_wall.SetCompoundStructure(cs_w)

        # Custom Floor
        f_temp = FilteredElementCollector(doc).OfClass(FloorType).FirstElement()
        bem_floor = f_temp.Duplicate("BEM_Floor_500mm")
        cs_f = bem_floor.GetCompoundStructure()
        cs_f.SetLayerWidth(0, 0.5 / 0.3048)
        bem_floor.SetCompoundStructure(cs_f)

        # 4. BUILD 9m x 9m ENVELOPE (Centerline 8.5m)
        print("LOG: Building Enclosure (8.5m Centerline for 9m Ext)...")
        c = 8.5 / 0.3048
        pts = [XYZ(0, 0, 0), XYZ(c, 0, 0), XYZ(c, c, 0), XYZ(0, c, 0)]

        for i in range(4):
            line = Line.CreateBound(pts[i], pts[(i + 1) % 4])
            # Create Wall
            wall = Wall.Create(doc, line, bem_wall.Id, lvls["BEM_P01_BASE"].Id, 5.5 / 0.3048, 0, False, False)
            # Constraints (String-based for safety)
            wall.LookupParameter("Base Offset").Set(-0.5 / 0.3048)  # Reach down to -1.5m
            wall.LookupParameter("Top Constraint").Set(lvls["BEM_P04_EAVE"].Id)
            wall.LookupParameter("Top Offset").Set(0)

        # 5. PLACE SLABS (9m x 9m)
        print("LOG: Placing Slabs...")
        f_sz = 9.0 / 0.3048
        off = 0.25 / 0.3048  # Aligns 9m slab with 8.5m wall centers
        f_pts = [XYZ(-off, -off, 0), XYZ(f_sz - off, -off, 0), XYZ(f_sz - off, f_sz - off, 0), XYZ(-off, f_sz - off, 0)]
        loop = CurveLoop()
        for i in range(4): loop.Append(Line.CreateBound(f_pts[i], f_pts[(i + 1) % 4]))

        Floor.Create(doc, [loop], bem_floor.Id, lvls["BEM_P01_BASE"].Id)  # Solera (-1.5 to -1.0)
        Floor.Create(doc, [loop], bem_floor.Id, lvls["BEM_P02_GROUND"].Id)  # Forjado (-0.5 to 0.0)
        Floor.Create(doc, [loop], bem_floor.Id, lvls["BEM_P03_ATTIC"].Id)  # Attic Floor (3.5 to 4.0)

        # 6. PLACE ROOMS (The HULC Thermal Zones)
        print("LOG: Injecting Thermal Zones (Rooms)...")
        uv = UV(4.5 / 0.3048, 4.5 / 0.3048)  # Center of 9x9m

        # P01_E01 (Cámara)
        r1 = doc.Create.NewRoom(lvls["BEM_P01_BASE"], uv)
        r1.Name = "P01_E01_CAMARA"
        r1.LookupParameter("Upper Limit").Set(lvls["BEM_P02_GROUND"].Id)

        # P02_E01 (Living)
        r2 = doc.Create.NewRoom(lvls["BEM_P02_GROUND"], uv)
        r2.Name = "P02_E01_LIVING"
        r2.LookupParameter("Upper Limit").Set(lvls["BEM_P03_ATTIC"].Id)

        t.Commit()
        print("✅ SUCCESS: HULC Geometry complete and Zones (Rooms) injected.")

    except Exception as e:
        t.RollBack()
        print("❌ ERROR: " + str(e))


build_final_model()