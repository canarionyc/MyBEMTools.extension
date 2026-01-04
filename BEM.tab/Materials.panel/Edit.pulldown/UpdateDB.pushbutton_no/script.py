# -*- coding: utf-8 -*-
import sys
import clr

try:
    clr.AddReference('RevitAPI')
    clr.AddReference('RevitServices')
    from Autodesk.Revit.DB import *
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument
    IN_REVIT = True
except ImportError:
    IN_REVIT = False
    print("This script must be run inside Revit.")

# ========================================================
# PDF SOURCE (Materials + Lambda)
# ========================================================
PDF_CONSTRUCTIONS = {
    "MURO EXTERIOR": {
        "layers": [
            ("Mortero de cemento", 0.03, 0.550),
            ("EPS Poliestireno", 0.14, 0.038),
            ("1 pie LP métrico o catalán", 0.24, 0.667),
            ("Mortero de cemento", 0.01, 0.550),
            ("Cámara de aire sin ventilar vertical", 0.05, 0.180),
            ("Placa de yeso laminado", 0.015, 0.250)
        ]
    },
    "MURO DE CÁMARA SANITARIA": {
        "layers": [
            ("Betún fieltro o lámina", 0.009, 0.230),
            ("1 pie LP métrico o catalán", 0.24, 0.667)
        ]
    },
    "TABIQUE INTERIOR": {
        "layers": [
            ("Placa de yeso laminado", 0.013, 0.250),
            ("MW Lana mineral", 0.04, 0.041)
        ]
    },
    "FORJADO INTERIOR (ACOND-ACOND)": {
        "layers": [
            ("Plaqueta de gres", 0.01, 2.300),
            ("Mortero de cemento", 0.05, 0.550),
            ("Mortero de cemento de difusión", 0.065, 0.550),
            ("XPS Expandido", 0.06, 0.034),
            ("FU entrevigado cerámico", 0.25, 0.908),
            ("Cámara de aire sin ventilar horizontal", 0.05, 0.160)
        ]
    },
    "FORJADO CON CÁMARA SANITARIA": {
        "layers": [
            ("Forjado Entrevigado EPS mecanizado", 0.30, 0.256),
            ("Lámina de cloruro de polivinilo (PVC)", 0.005, 0.170)
        ]
    },
    "SOLERA DE CÁMARA SANITARIA": {
        "layers": [
            ("Hormigón en masa", 0.08, 1.650),
            ("Lámina PVC", 0.003, 0.170),
            ("Arena y grava", 0.12, 2.000)
        ]
    },
    "CUBIERTA INCLINADA DE TEJA": {
        "layers": [
            ("Teja de arcilla cocida", 0.015, 1.000),
            ("Cámara aire ventilada, flujo ascend.", 0.05, 0.060),
            ("Betún fieltro o lámina", 0.01, 0.230)
        ]
    }
}

def update_material_model_param():
    if not IN_REVIT: return
    
    TransactionManager.Instance.EnsureInTransaction(doc)
    print("--- UPDATING MATERIAL SCHEDULE DATA ---")
    
    # Track processed to avoid duplicates
    processed_mats = set()
    
    for key, data in PDF_CONSTRUCTIONS.items():
        for layer in data["layers"]:
            mat_name = layer[0]
            k_val = layer[2]
            
            if mat_name in processed_mats: continue
            
            # Find Material
            col = FilteredElementCollector(doc).OfClass(Material)
            target_mat = None
            for m in col:
                if m.Name == mat_name:
                    target_mat = m
                    break
            
            if target_mat:
                # Set 'Model' parameter to the Lambda value
                try:
                    # BuiltInParameter for "Model" property in Identity Data
                    p = target_mat.get_Parameter(BuiltInParameter.ALL_MODEL_MODEL)
                    if p:
                        val_str = str(k_val)
                        p.Set(val_str)
                        print(f"Updated {mat_name}: Model = {val_str}")
                    else:
                        print(f"Param not found for {mat_name}")
                except Exception as e:
                    print(f"Error {mat_name}: {e}")
            
            processed_mats.add(mat_name)

    TransactionManager.Instance.TransactionTaskDone()
    print("\nDone. You can now schedule 'Material: Model' as Conductivity.")

update_material_model_param()