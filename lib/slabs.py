#! python 3
from pprint import pprint

#%% SETUP AND IMPORTS
import clr
# noinspection PyUnresolvedReferences
clr.AddReference("RevitAPI")
# noinspection PyUnresolvedReferences
clr.AddReference("RhinoCommon")

import Rhino.Geometry as rg
from Autodesk.Revit.DB import Document, Level, FilteredElementCollector, Transaction, Floor, FloorType
# noinspection PyUnresolvedReferences
import RhinoInside.Revit as rir
# noinspection PyUnresolvedReferences
from RhinoInside.Revit.Convert.Geometry import GeometryEncoder


# Reference the active Revit document
doc = rir.Revit.ActiveDBDocument


# %% GEOMETRY EXTRACTION

def extract_bottom_profile_from_solid(extrusion: rg.Extrusion) -> list[rg.Curve]:
    """
    Converts a Rhino Extrusion into a Brep, identifies the bottom face,
    and extracts its outer boundary curves.
    """
    brep = extrusion.ToBrep(True)

    for face in brep.Faces:
        # 1. Find the midpoints of the surface domains
        u_mid = face.Domain(0).Mid
        v_mid = face.Domain(1).Mid

        # 2. CORRECTED: Ask Rhino directly for the normal vector
        normal = face.NormalAt(u_mid, v_mid)

        # 3. 'normal' is now a single Vector3d, so evaluating .Z works perfectly
        if normal.Z < -0.5:
            boundary_curve = face.OuterLoop.To3dCurve()

            segments = boundary_curve.DuplicateSegments()
            if segments:
                return list(segments)
            else:
                return [boundary_curve]

    return []

# %% REVIT SLAB CREATION
def create_revit_floor_from_extrusion(
        extrusion: rg.Extrusion,
        level: Level,
        floor_type: FloorType
) -> Floor:
    """
    Extracts the profile from a Rhino Extrusion and generates a native Revit Floor.
    """
    # Extract the Rhino base curves from the 3D object
    rhino_curves = extract_bottom_profile_from_solid(extrusion)
    if not rhino_curves:
        raise ValueError("Could not find a valid bottom profile on the extrusion.")

    t = Transaction(doc, "Generate Slab from Rhino Extrusion")
    t.Start()

    try:
        # 1. Create a Revit CurveLoop
        curve_loop = CurveLoop()
        for crv in rhino_curves:
            revit_curve = GeometryEncoder.ToCurve(crv)
            curve_loop.Append(revit_curve)

        # 2. Revit Floor.Create requires a .NET List of CurveLoops
        loop_list = List[CurveLoop]()
        loop_list.Add(curve_loop)

        # 3. Generate the native Floor
        # Signature: Floor.Create(Document, IList<CurveLoop>, ElementId floorTypeId, ElementId levelId)
        new_floor = Floor.Create(doc, loop_list, floor_type.Id, level.Id)

        t.Commit()
        pprint("Successfully created native Revit Floor.")
        return new_floor

    except Exception as e:
        t.RollBack()
        pprint(f"Transaction failed: {e}")
        return None