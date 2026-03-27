#! python2
# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit import DB
from pyrevit import script, revit

doc = __revit__.ActiveUIDocument.Document
output = script.get_output()

def cm_to_ft(cm):
    """Converts centimeters to Revit's internal decimal feet."""
    return cm / 30.48

def modify_structure_by_function(new_type, function_modifications):
    """Modifies layer thickness based on their Revit Core Function."""
    comp_struct = new_type.GetCompoundStructure()
    if not comp_struct:
        return False
    
    layers = comp_struct.GetLayers()
    modified = False
    
    for i, layer in enumerate(layers):
        if layer.Function in function_modifications:
            new_cm = function_modifications[layer.Function]
            comp_struct.SetLayerWidth(i, cm_to_ft(new_cm))
            modified = True
            
    if modified:
        new_type.SetCompoundStructure(comp_struct)
        return True
    return False

def duplicate_and_modify_type(base_name, new_name, modifications, type_class):
    """Safely handles the duplication logic."""
    base_type = None
    for t in DB.FilteredElementCollector(doc).OfClass(type_class).ToElements():
        if base_name in t.Name:
            base_type = t
            break
            
    if not base_type:
        output.print_md("❌ **No encontrado:** Falta el tipo base '{}'".format(base_name))
        return None
        
    for t in DB.FilteredElementCollector(doc).OfClass(type_class).ToElements():
        if t.Name == new_name:
            output.print_md("⚠️ **Ya existe:** '{}'".format(new_name))
            return t

    try:
        new_type = base_type.Duplicate(new_name)
        success = modify_structure_by_function(new_type, modifications)
        if success:
            output.print_md("✅ **Éxito:** '{}' creado con capas actualizadas.".format(new_name))
        else:
            output.print_md("⚠️ **Aviso:** '{}' creado, pero no se modificaron capas.".format(new_name))
        return new_type
    except Exception as e:
        output.print_md("❌ **Error** al crear '{}': {}".format(new_name, str(e)))
        return None


# --- MAIN EXECUTION ---
output.print_md("# 🏗️ Duplicación Robusta de Tipos Base")

# The PyRevit Context Manager: This guarantees the transaction closes!
try:
    with revit.Transaction("BEM: Duplicar Tipos Base (Robust)"):
        
        # 1. Muro de 20 cm
        duplicate_and_modify_type(
            base_name="Muro básico bloque hormigón enfos, trasd. PYL-27 cm.",
            new_name="Muro básico, bloque hormigón enfos. trasd. PYL - 20 cm.",
            modifications={
                DB.MaterialFunctionAssignment.Structure: 12.0,
                DB.MaterialFunctionAssignment.Insulation: 5.0
            },
            type_class=DB.WallType
        )

        # 2. Forjado Bovedilla 35 cm
        duplicate_and_modify_type(
            base_name="Suelo, con bovedilla cerámica de 34 cm.",
            new_name="Suelo, con bovedilla cerámica - 35 cm.",
            modifications={
                DB.MaterialFunctionAssignment.Structure: 5.0
            },
            type_class=DB.FloorType
        )

        # 3. Recrecido Base Armarios 10 cm
        duplicate_and_modify_type(
            base_name="Suelo, Acera de 19 cm.",
            new_name="Suelo, Recrecido base armarios 10 cm.",
            modifications={
                DB.MaterialFunctionAssignment.Structure: 7.0
            },  
            type_class=DB.FloorType
        )

        # 4. Porche y Terraza 17 cm
        duplicate_and_modify_type(
            base_name="Suelo, Acera de 19 cm.",
            new_name="Suelo, Porche y Terraza 17 cm.",
            modifications={
                DB.MaterialFunctionAssignment.Structure: 14.0
            },
            type_class=DB.FloorType
        )
except Exception as main_e:
    output.print_md("🚨 **Error Crítico en la Transacción:** {}".format(str(main_e)))

output.print_md("---")