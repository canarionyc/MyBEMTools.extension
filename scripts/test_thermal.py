# -*- coding: utf-8 -*-
"""Verifies thermal properties of slabs for MyBEMTools."""
from pyrevit import revit, DB, script

# Initialize output window
output = script.get_output()
doc = revit.doc

def get_thermal_info():
    # 1. Collect all Floors (includes Foundation Slabs)
    collector = DB.FilteredElementCollector(doc)\
                  .OfCategory(DB.BuiltInCategory.OST_Floors)\
                  .WhereElementIsNotElementType()

    output.print_md("## --- BEM THERMAL CHECK ---")
    
    for el in collector:
        # 2. Get the Type (where thermal properties live)
        el_type = doc.GetElement(el.GetTypeId())
        
        # 3. Access Thermal Properties
        # Revit 2025 uses the ThermalProperties asset on the ElementType
        tp = el_type.ThermalProperties
        
        # 4. Handle Revit 2025 ElementId (.Value is Int64)
        el_id = el.Id.Value 
        
        name = revit.query.get_name(el)
        type_name = revit.query.get_name(el_type)

        if tp:
            # R-Value (Thermal Resistance)
            r_value = tp.ThermalResistance
            # U-Value (Heat Transfer Coefficient)
            u_value = tp.HeatTransferCoefficient
            
            output.print_md("**Element ID:** `{}` | **Name:** {}".format(el_id, name))
            print("   > Type: {}".format(type_name))
            print("   > R-Value: {:.4f} (m²·K/W)".format(r_value))
            print("   > U-Value: {:.4f} (W/m²·K)".format(u_value))
            print("-" * 50)
        else:
            output.print_md("❌ **Element ID:** `{}` | **{}**".format(el_id, name))
            print("   > WARNING: No Thermal Asset assigned to this type.")
            print("-" * 50)

if __name__ == "__main__":
    get_thermal_info()