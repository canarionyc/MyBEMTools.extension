#%% IMPORTS AND SETUP
import sys
import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from pyrevit import revit

FT_TO_M = 0.3048

def log(msg): # type: (str) -> None
    """Robust logger that forces output to the console immediately"""
    sys.stdout.write("--- [BEM LOG]: {} ---\n".format(msg))
    sys.stdout.flush()

#%% COORDINATE AUDIT
def audit_spatial_extents(doc): # type: (Document) -> None
    """Scans the document for base points and linked bounding boxes."""
    log("============================================================")
    log(" SPATIAL EXTENTS AUDIT: {}".format(doc.Title))
    log("============================================================")
    
    # 1. Audit Revit Base Points
    pbp = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ProjectBasePoint).FirstElement()
    sp = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_SharedBasePoint).FirstElement()
    
    if pbp:
        pos = pbp.get_BoundingBox(None).Min
        log("PROJECT BASE POINT : X={:.2f}m, Y={:.2f}m, Z={:.2f}m".format(
            pos.X * FT_TO_M, pos.Y * FT_TO_M, pos.Z * FT_TO_M))
    
    if sp:
        pos = sp.get_BoundingBox(None).Min
        log("SURVEY POINT       : X={:.2f}m, Y={:.2f}m, Z={:.2f}m".format(
            pos.X * FT_TO_M, pos.Y * FT_TO_M, pos.Z * FT_TO_M))
            
    log("------------------------------------------------------------")

    # 2. Audit Link Bounding Boxes (Hunting for Rogue Elements)
    links = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    
    if not links:
        log("[No Linked Models Found]")
    else:
        for link in links:
            log("> LINK INSTANCE: {}".format(link.Name))
            bbox = link.get_BoundingBox(None)
            
            if bbox:
                min_pt = bbox.Min
                max_pt = bbox.Max
                
                size_x = (max_pt.X - min_pt.X) * FT_TO_M
                size_y = (max_pt.Y - min_pt.Y) * FT_TO_M
                size_z = (max_pt.Z - min_pt.Z) * FT_TO_M
                
                log("  - BoundingBox Min: X={:.2f}m, Y={:.2f}m, Z={:.2f}m".format(
                    min_pt.X * FT_TO_M, min_pt.Y * FT_TO_M, min_pt.Z * FT_TO_M))
                log("  - BoundingBox Max: X={:.2f}m, Y={:.2f}m, Z={:.2f}m".format(
                    max_pt.X * FT_TO_M, max_pt.Y * FT_TO_M, max_pt.Z * FT_TO_M))
                log("  - Physical Extent: {:.2f}m x {:.2f}m x {:.2f}m".format(
                    size_x, size_y, size_z))
                
                if size_x > 10000 or size_y > 10000:
                    log("  [!] WARNING: The physical size of this link is massive. You have a rogue distant element.")
            else:
                log("  [No geometric Bounding Box found for link]")

    log("============================================================")
    log("AUDIT COMPLETE")

#%% MAIN EXECUTION
if __name__ == "__main__":
    current_doc = None
    try:
        if '__models__' in globals() and __models__:
            model_path = __models__[0]
            current_doc = revit.app.OpenDocumentFile(model_path)
        if not current_doc:
            current_doc = revit.doc
            
        if current_doc:
            audit_spatial_extents(current_doc)
        else:
            log("FATAL: No document acquired.")
    except Exception as e:
        log("Execution Error: {}".format(e))