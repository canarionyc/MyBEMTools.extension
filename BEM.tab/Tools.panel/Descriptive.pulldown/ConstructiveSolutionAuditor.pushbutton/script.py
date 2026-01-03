# -*- coding: utf-8 -*-
from pyrevit import revit, DB, script

doc = revit.doc
output = script.get_output()

# Targeted ID for your Solera
TARGET_ID_INT = 1659623 

print("--- BEM CONSTRUCTIVE AUDIT: INTERACTIVE LINKS ---")

# 1. Get the Main Element
target_id = DB.ElementId(TARGET_ID_INT)
el = doc.GetElement(target_id)

if el:
    el_type = doc.GetElement(el.GetTypeId())
    
    # LINKIFY the main element
    print("AUDITING: {} [{}]".format(el.Name, output.linkify(el.Id)))
    print("TYPE:     {}".format(el_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()))
    print("=" * 60)

    if hasattr(el_type, "GetCompoundStructure"):
        comp_struct = el_type.GetCompoundStructure()
        
        if comp_struct:
            layers = comp_struct.GetLayers()
            for i, layer in enumerate(layers):
                mat_id = layer.MaterialId
                thick = layer.Width * 304.8
                
                print("\n[LAYER {}] - {:.2f}mm".format(i + 1, thick))
                
                if mat_id != DB.ElementId.InvalidElementId:
                    material = doc.GetElement(mat_id)
                    
                    # LINKIFY the Material
                    print("  - MATERIAL: {} [{}]".format(material.Name, output.linkify(mat_id)))
                    
                    # Check for Thermal Asset
                    thermal_id = material.ThermalAssetId
                    if thermal_id != DB.ElementId.InvalidElementId:
                        # LINKIFY the Thermal Asset
                        print("  - THERMAL ASSET: FOUND [{}]".format(output.linkify(thermal_id)))
                        
                        # Fetch the actual thermal properties for the report
                        asset_elem = doc.GetElement(thermal_id)
                        # Accessing the specific BEM parameters via the PropertySet
                        pa = asset_elem.get_Parameter(DB.BuiltInParameter.THERMAL_MATERIAL_CONDUCTIVITY)
                        if pa:
                            print("    > Conductivity (λ): {:.4f} W/(m·K)".format(pa.AsDouble()))
                    else:
                        print("  - THERMAL ASSET: [MISSING]")
                else:
                    print("  - MATERIAL: <NO MATERIAL ASSIGNED>")

print("Done auditing constructive layers.")