# -*- coding: utf-8 -*-
import sys
import os
import clr

try:
    clr.AddReference('RevitAPI')
    from Autodesk.Revit.DB import *
    from RevitServices.Persistence import DocumentManager
    doc = DocumentManager.Instance.CurrentDBDocument
    IN_REVIT = True
except ImportError:
    IN_REVIT = False

# ========================================================
# CONFIGURATION
# ========================================================
user_home = os.environ['ONEDRIVE']
desktop = os.path.join(user_home, "Desktop")
OUTPUT_FILE = os.path.join(desktop, "CTE_Layer_Report.csv")

def m2ft(meters): return meters * 3.28084
def ft2m(feet): return feet * 0.3048

def get_safe_mat_name(doc, mat_id):
    if mat_id == ElementId.InvalidElementId: return "No Material"
    try:
        return doc.GetElement(mat_id).Name
    except:
        return "Unknown Material"

def run_layer_export():
    if not IN_REVIT: return

    # Categories to scan
    cats = [
        (WallType, "Wall"),
        (FloorType, "Floor"),
        (RoofType, "Roof")
    ]
    
    lines = []
    # Header
    lines.append("Category,Type Name,Total Thickness (m),Layer Index,Material Name,Layer Thickness (m),Conductivity (Model Param)")

    print("--- SCANNING TYPES ---")

    for class_type, cat_name in cats:
        col = FilteredElementCollector(doc).OfClass(class_type).WhereElementIsElementType()
        
        for t in col:
            # 1. Get Type Name safely
            try:
                t_name = t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            except:
                t_name = t.Name
            
            if not t_name: t_name = "Unnamed Type"

            # 2. Get Compound Structure (The Layers)
            try:
                cs = t.GetCompoundStructure()
            except:
                cs = None
                
            if not cs: continue 

            # --- FIX: Use cs.GetWidth() instead of t.Width ---
            # This works for Walls, Floors, and Roofs
            total_width = ft2m(cs.GetWidth())
            
            layers = cs.GetLayers()
            
            print(f"Exporting: {t_name}")

            # 3. Iterate Layers
            for i, layer in enumerate(layers):
                width_m = ft2m(layer.Width)
                mat_name = get_safe_mat_name(doc, layer.MaterialId)
                
                # Try to get Lambda from the Material's "Model" parameter
                lambda_val = ""
                if layer.MaterialId != ElementId.InvalidElementId:
                    try:
                        mat = doc.GetElement(layer.MaterialId)
                        p = mat.get_Parameter(BuiltInParameter.ALL_MODEL_MODEL)
                        if p and p.HasValue: lambda_val = p.AsString()
                    except: pass
                
                # CSV Format
                row = f'"{cat_name}","{t_name}",{total_width:.4f},{i+1},"{mat_name}",{width_m:.4f},"{lambda_val}"'
                lines.append(row)

    # WRITE TO FILE
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        print(f"\nSuccess! Exported to: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing file: {e}")

run_layer_export()