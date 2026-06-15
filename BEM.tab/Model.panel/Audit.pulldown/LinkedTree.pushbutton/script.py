# -*- coding: utf-8 -*-
import sys
import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from pyrevit import revit

# Unit Conversion factors
FT_TO_M = 0.3048
FT_TO_MM = 304.8


def log(msg, error=False):
    """Robust logger that forces output to the console immediately"""
    stream = sys.stderr if error else sys.stdout
    stream.write("--- [BEM LOG]: {} ---\n".format(msg))
    stream.flush()


def get_parameter_value(param):
    """Safely extracts the value of a Revit parameter"""
    if not param or not param.HasValue:
        return "None"
    
    stype = param.StorageType
    if stype == StorageType.String:
        return param.AsString()
    elif stype == StorageType.Double:
        return "{:.6f}".format(param.AsDouble())
    elif stype == StorageType.Integer:
        return str(param.AsInteger())
    elif stype == StorageType.ElementId:
        return str(param.AsElementId().IntegerValue)
    return param.AsValueString()


log("PROCESS STARTED")

# 1. Document Acquisition
doc = None
try:
    if '__models__' in globals() and __models__:
        model_path = __models__[0]
        log("Opening model headlessly: {}".format(model_path))
        doc = revit.app.OpenDocumentFile(model_path)

    if not doc:
        doc = revit.doc  # Fallback for pyRevit UI

    if doc:
        log("Successfully linked to HOST: {}".format(doc.Title))
    else:
        log("FATAL: No document could be acquired.", True)
        sys.exit(1)
except Exception as e:
    log("Initialization Error: {}".format(e), True)
    sys.exit(1)


# ==============================================================================
# LINKED MODELS AUDIT (IFC)
# ==============================================================================
links = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()

log("\n" + "=" * 60)
log(" LINKED MODELS & IFC METADATA")
log("-" * 60)

if not links:
    log("  [No Linked Models Found]")
else:
    for link in links:
        log("\n  > LINK INSTANCE: {}".format(link.Name))
        
        # 1. Extract Link Type Metadata
        link_type = doc.GetElement(link.GetTypeId())
        if link_type:
            log("    [Link Type IFC Parameters]")
            for param in link_type.Parameters:
                p_name = param.Definition.Name
                if "Pset_" in p_name or "Ifc" in p_name or "Export" in p_name:
                    log("      - {}: {}".format(p_name, get_parameter_value(param)))

        # 2. Access the Linked Database
        link_doc = link.GetLinkDocument()
        if not link_doc:
            log("    [Link Document is unloaded or inaccessible]")
            continue
            
        log("\n    [Linked Database Audit: {}]".format(link_doc.Title))
        
        # Extract Project Information from inside the IFC link
        proj_info = link_doc.ProjectInformation
        if proj_info:
            log("    [Project Information]")
            log("      - Name: {}".format(proj_info.Name))
            log("      - Number: {}".format(proj_info.Number))
            log("      - Status: {}".format(proj_info.Status))
            # Extract Pset parameters attached to the Project Information
            for param in proj_info.Parameters:
                p_name = param.Definition.Name
                if "Pset_" in p_name or "BIM_" in p_name:
                    log("      - {}: {}".format(p_name, get_parameter_value(param)))

        l_levels = FilteredElementCollector(link_doc).OfCategory(BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()
        l_walls = FilteredElementCollector(link_doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType().ToElements()
        
        log("\n    Found inside link: {} Levels, {} Walls".format(len(l_levels), len(l_walls)))
        
        # 3. Map Walls using IFC Spatial Container instead of Revit LevelId
        container_map = {}
        for w in l_walls:
            container_param = w.LookupParameter("IfcSpatialContainer")
            container_name = container_param.AsString() if (container_param and container_param.HasValue) else "Unassigned"
            
            if container_name not in container_map:
                container_map[container_name] = []
            container_map[container_name].append(w)

        # 4. Print the Walls organized by their IFC Storey
        for container, walls_in_container in container_map.items():
            log("\n      IFC CONTAINER: [{}]".format(container))
            log("        > WALLS ({}):".format(len(walls_in_container)))

            for w in walls_in_container:
                ifc_name_param = w.LookupParameter("IfcName")
                wall_name = ifc_name_param.AsString() if (ifc_name_param and ifc_name_param.HasValue) else w.Name

                # SAFELY CHECK LOCATION TYPE
                loc = w.Location
                if isinstance(loc, LocationCurve):
                    curve = loc.Curve
                    pt1 = curve.GetEndPoint(0)
                    pt2 = curve.GetEndPoint(1)
                    x1, y1 = pt1.X * FT_TO_MM, pt1.Y * FT_TO_MM
                    x2, y2 = pt2.X * FT_TO_MM, pt2.Y * FT_TO_MM
                    log("          - Wall ID {}: [{}] Start({:.1f}, {:.1f}) to End({:.1f}, {:.1f}) mm".format(w.Id,
                        wall_name, x1, y1, x2, y2))
                else:
                    # Fallback for DirectShapes / Breps without a baseline curve
                    log("          - Wall ID {}: [{}] (DirectShape/Brep - No axis curve)".format(w.Id, wall_name))

log("\n" + "=" * 60)
log("AUDIT COMPLETE")