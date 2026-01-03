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
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *

doc = __revit__.ActiveUIDocument.Document


def finalize_thermal_only():
    print("--- 🔍 BEM FINALIZER: THERMAL COMMIT MODE ---")

    t = Transaction(doc, "BEM Thermal Data")
    t.Start()

    try:
        # 1. GET TYPES
        w_types = FilteredElementCollector(doc).OfClass(WallType).ToElements()
        f_types = FilteredElementCollector(doc).OfClass(FloorType).ToElements()

        bem_wall = next((wt for wt in w_types if
                         "BEM_Wall_500mm" in wt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()), None)
        bem_floor = next((ft for ft in f_types if
                          "BEM_Floor_500mm" in ft.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()), None)

        # 2. INJECT THERMAL NAMES
        def update_mat(etype, label, u_val):
            if not etype: return
            cs = etype.GetCompoundStructure()
            m_id = cs.GetMaterialId(0)
            if m_id == ElementId.InvalidElementId:
                m_id = Material.Create(doc, "BEM_Mat_" + label)
                cs.SetMaterialId(0, m_id)
                etype.SetCompoundStructure(cs)
            mat = doc.GetElement(m_id)
            k_val = round(u_val * 0.5, 4)
            mat.Name = "BEM_{}_U_{}_k_{}".format(label, str(u_val).replace(".", ""), str(k_val).replace(".", ""))
            print(">>> ✅ SAVED: " + mat.Name)

        update_mat(bem_wall, "ENVOLVENTE_WALL", 0.22)
        update_mat(bem_floor, "FORJADO_SANITARIO", 0.15)

        t.Commit()
        print("\n🏆 THERMAL DATA PERMANENTLY SAVED. Proceeding to Roof attempt...")

        # 3. ROOF ATTEMPT (IN A SEPARATE TRY BLOCK)
        try:
            t_roof = Transaction(doc, "BEM Roof Attempt")
            t_roof.Start()

            lvls = FilteredElementCollector(doc).OfClass(Level).ToElements()
            lvl_eave = next((l for l in lvls if "P04_EAVE" in l.Name), None)
            r_type = FilteredElementCollector(doc).OfClass(RoofType).FirstElement()

            # Using a safer way to call the creation factory
            f_sz, off = 9.0 / 0.3048, 0.25 / 0.3048
            pts = [XYZ(-off, -off, 0), XYZ(f_sz - off, -off, 0), XYZ(f_sz - off, f_sz - off, 0),
                   XYZ(-off, f_sz - off, 0)]
            c_arr = CurveArray()
            for i in range(4): c_arr.Append(Line.CreateBound(pts[i], pts[(i + 1) % 4]))

            m_curves = ModelCurveArray()
            # If this line fails, it won't undo the Thermal Data above!
            new_roof = doc.Create.NewFootprintRoof(c_arr, lvl_eave, r_type, m_curves)

            for c in m_curves:
                new_roof.set_DefinesSlope(c, True)
                new_roof.set_Slope(c, 1.0)  # 45 deg

            t_roof.Commit()
            print("✅ ROOF CREATED SUCCESSFULLY.")
        except Exception as e:
            print("\n⚠️ ROOF FAILED: " + str(e))
            print("Action: Please create the roof manually (instructions below).")

    except Exception as e:
        print("❌ FATAL ERROR: " + str(e))
        t.RollBack()


finalize_thermal_only()