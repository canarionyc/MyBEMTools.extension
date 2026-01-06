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
# 1. MATERIALS & OPAQUE CONSTRUCTIONS (Updated with TAG)
# ========================================================
# Added the "CTE" tag to the logic
TAG_VALUE = "CTE"

PDF_CONSTRUCTIONS = {
    "MURO EXTERIOR": {
        "category": "Wall",
        "layers": [
            ("Mortero de cemento", 0.03, 0.550),
            ("EPS Poliestireno", 0.14, 0.038),
            ("1 pie LP métrico o catalán", 0.24, 0.667),
            ("Mortero de cemento", 0.01, 0.550),
            ("Cámara de aire sin ventilar vertical", 0.05, 0.180),
            ("Placa de yeso laminado", 0.015, 0.250),
            ("Placa de yeso laminado", 0.015, 0.250)
        ]
    },
    "MURO DE CÁMARA SANITARIA": {
        "category": "Wall",
        "layers": [
            ("Betún fieltro o lámina", 0.009, 0.230),
            ("1 pie LP métrico o catalán", 0.24, 0.667)
        ]
    },
    "TABIQUE INTERIOR": {
        "category": "Wall",
        "layers": [
            ("Placa de yeso laminado", 0.013, 0.250),
            ("Placa de yeso laminado", 0.013, 0.250),
            ("MW Lana mineral", 0.04, 0.041),
            ("Placa de yeso laminado", 0.013, 0.250),
            ("Placa de yeso laminado", 0.013, 0.250)
        ]
    },
    "FORJADO INTERIOR (ACOND-ACOND)": {
        "category": "Floor",
        "layers": [
            ("Plaqueta de gres", 0.01, 2.300),
            ("Mortero de cemento", 0.05, 0.550),
            ("Mortero de cemento de difusión", 0.065, 0.550),
            ("XPS Expandido", 0.06, 0.034),
            ("FU entrevigado cerámico", 0.25, 0.908),
            ("Cámara de aire sin ventilar horizontal", 0.05, 0.160),
            ("Placa de yeso laminado", 0.015, 0.250)
        ]
    },
    "FORJADO INTERIOR (ACOND-NO HAB)": {
        "category": "Floor",
        "layers": [
            ("Plaqueta de gres", 0.01, 2.300),
            ("Mortero de cemento", 0.055, 0.550),
            ("XPS Expandido", 0.12, 0.034),
            ("FU entrevigado cerámico", 0.25, 0.908),
            ("Cámara de aire sin ventilar horizontal", 0.05, 0.160),
            ("Placa de yeso laminado", 0.015, 0.250)
        ]
    },
    "FORJADO CON CÁMARA SANITARIA": {
        "category": "Floor",
        "layers": [
            ("Plaqueta de gres", 0.01, 2.300),
            ("Mortero de cemento", 0.025, 0.550),
            ("Mortero de cemento de difusión", 0.06, 0.550),
            ("XPS Expandido", 0.10, 0.034),
            ("Forjado Entrevigado EPS mecanizado", 0.30, 0.256),
            ("Lámina de cloruro de polivinilo (PVC)", 0.005, 0.170)
        ]
    },
    "SOLERA DE CÁMARA SANITARIA": {
        "category": "Floor",
        "layers": [
            ("Hormigón en masa", 0.08, 1.650),
            ("Lámina PVC", 0.003, 0.170),
            ("Arena y grava", 0.12, 2.000)
        ]
    },
    "CUBIERTA INCLINADA DE TEJA": {
        "category": "Roof",
        "layers": [
            ("Teja de arcilla cocida", 0.015, 1.000),
            ("Cámara aire ventilada, flujo ascend.", 0.05, 0.060),
            ("XPS Expandido", 0.16, 0.034),
            ("Betún fieltro o lámina", 0.01, 0.230),
            ("Forjado Entrevigado EPS mecanizado", 0.25, 0.266),
            ("Placa de yeso laminado", 0.015, 0.250)
        ]
    }
}

# ========================================================
# 2. OPENINGS (WINDOWS & DOORS) FROM PDF
# ========================================================
# Data extracted from PDF pages 38-40
OPENINGS_DATA = {
    "Ventana N-E (CTE)": {
        "category": BuiltInCategory.OST_Windows,
        "description": "Vidrio: 4-16Ar-4 (Low-E <0.03), Ug=1.0, g=0.61 | Marco: PVC, Uf=1.5",
        "u_val": 1.5,  # Approximate total Uw or Frame U
        "tag": "CTE"
    },
    "Ventana S-O (CTE)": {
        "category": BuiltInCategory.OST_Windows,
        "description": "Vidrio: 4-16Ar-4 (Low-E <0.03), Ug=1.0, g=0.42 | Marco: PVC, Uf=1.5",
        "u_val": 1.5,
        "tag": "CTE"
    },
    "Lucernario S-E (CTE)": {
        "category": BuiltInCategory.OST_Windows,  # Usually modeled as Windows or Roof Windows
        "description": "Vidrio: 4-16Ar-4, Ug=1.0, g=0.42 | Marco: Madera, Uf=2.4",
        "u_val": 2.4,
        "tag": "CTE"
    },
    "Lucernario N (CTE)": {
        "category": BuiltInCategory.OST_Windows,
        "description": "Vidrio: 4-16Ar-4, Ug=1.0, g=0.61 | Marco: Madera, Uf=2.4",
        "u_val": 2.4,
        "tag": "CTE"
    },
    "Puerta Acceso (CTE)": {
        "category": BuiltInCategory.OST_Doors,
        "description": "Marco: Madera Densidad Media-Alta, Uf=2.2 | Opaca",
        "u_val": 2.2,
        "tag": "CTE"
    }
}


# ========================================================
# HELPER FUNCTIONS
# ========================================================
def m2ft(meters):
    return meters * 3.28084


def ensure_thermal_asset(doc, mat_element, k_val_si):
    therm_id = mat_element.ThermalAssetId
    if therm_id != ElementId.InvalidElementId: return

    try:
        asset_name = "Thermal_" + mat_element.Name
        t_asset = ThermalAsset(asset_name, ThermalMaterialType.Solid)
        val_internal = k_val_si * 0.3048
        t_asset.ThermalConductivity = val_internal
        pse = PropertySetElement.Create(doc, t_asset)
        mat_element.ThermalAssetId = pse.Id
    except Exception as e:
        print("Warning: Thermal set failed for {mat_element.Name}: {e}")


def get_or_create_material(doc, mat_name, k_val):
    col = FilteredElementCollector(doc).OfClass(Material)
    found_mat = None
    for m in col:
        if m.Name == mat_name:
            found_mat = m
            break

    if not found_mat:
        new_id = Material.Create(doc, mat_name)
        found_mat = doc.GetElement(new_id)

    # 1. Ensure Thermal
    ensure_thermal_asset(doc, found_mat, k_val)

    # 2. Ensure TAG (Comments)
    try:
        p_comm = found_mat.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION)  # Description
        # Or Comments: BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS
        # Materials use ALL_MODEL_INSTANCE_COMMENTS for "Comments" field in UI? No, usually distinct.
        # Let's try finding parameter by name to be safe/lazy, or use specific BuiltIn

        # In Revit Materials, the "Comments" field is 'ALL_MODEL_INSTANCE_COMMENTS'
        p = found_mat.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if p and not p.IsReadOnly:
            p.Set(TAG_VALUE)
    except:
        pass

    return found_mat.Id


def get_template_type(doc, kind):
    # Kind is 'Wall', 'Floor', 'Roof'
    def get_safe_name(elem):
        try:
            p = elem.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
            if p and p.HasValue: return p.AsString()
            return elem.Name
        except:
            return "UNKNOWN"

    col = FilteredElementCollector(doc)
    if kind == 'Wall':
        col.OfClass(WallType)
    elif kind == 'Floor':
        col.OfClass(FloorType)
    elif kind == 'Roof':
        col.OfClass(RoofType)
    col.WhereElementIsElementType()

    elements = list(col.ToElements())
    selected = None

    for t in elements:
        nm = get_safe_name(t)
        if "Generic" in nm or "Genérico" in nm or "Default" in nm:
            selected = t
            break

    if not selected and elements: selected = elements[0]
    return selected


def create_opening_types(doc):
    print("\n--- 3. CREATING WINDOW & DOOR TYPES ---")

    # Helper to find a family to duplicate
    def get_family_symbol(cat_enum):
        col = FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsElementType()
        for s in col:
            # We want a symbol (Type), not the Family itself
            if isinstance(s, FamilySymbol):
                return s
        return None

    for name, info in OPENINGS_DATA.items():
        cat = info['category']

        # 1. Find a template to duplicate
        tmpl = get_family_symbol(cat)
        if not tmpl:
            print("SKIP {name}: No loaded families found for category.")
            continue

        # 2. Check if Type exists
        found_type = None
        col = FilteredElementCollector(doc).OfCategory(cat).WhereElementIsElementType()
        for t in col:
            # Check name
            try:
                t_name = t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
                if t_name == name:
                    found_type = t
                    break
            except:
                pass

        # 3. Duplicate
        if not found_type:
            try:
                found_type = tmpl.Duplicate(name)
                print("CREATED: {name}")
            except Exception as e:
                print("ERROR creating {name}: {e}")
                continue
        else:
            print("EXISTS: {name}")

        # 4. Set Metadata (Description & Tag)
        try:
            # Description
            p_desc = found_type.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION)
            if p_desc: p_desc.Set(info['description'])

            # Type Comments (Tag)
            p_comm = found_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
            if p_comm: p_comm.Set(info['tag'])

        except Exception as e:
            print("  -> Warn: Could not set params for {name}")


def build_library():
    if not IN_REVIT: return

    TransactionManager.Instance.EnsureInTransaction(doc)
    print("--- 1. BUILDING MATERIALS (WITH TAGS) ---")

    material_cache = {}
    for type_name, data in PDF_CONSTRUCTIONS.items():
        for layer in data["layers"]:
            mat_name = layer[0]
            k_val = layer[2]
            if mat_name not in material_cache:
                mid = get_or_create_material(doc, mat_name, k_val)
                material_cache[mat_name] = mid
    print("Materials OK.")

    print("\n--- 2. BUILDING WALL/FLOOR/ROOF TYPES ---")

    wall_tmpl = get_template_type(doc, 'Wall')
    floor_tmpl = get_template_type(doc, 'Floor')
    roof_tmpl = get_template_type(doc, 'Roof')

    class_map = {'Wall': WallType, 'Floor': FloorType, 'Roof': RoofType}

    for type_name, data in PDF_CONSTRUCTIONS.items():
        kind = data["category"]
        tmpl = None
        if kind == 'Wall':
            tmpl = wall_tmpl
        elif kind == 'Floor':
            tmpl = floor_tmpl
        elif kind == 'Roof':
            tmpl = roof_tmpl

        if not tmpl: continue

        target_class = class_map.get(kind)
        target_type = None

        # Find existing
        col = FilteredElementCollector(doc).OfClass(target_class).WhereElementIsElementType()
        for t in col:
            t_name = "UNKNOWN"
            try:
                t_name = t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            except:
                try:
                    t_name = t.Name
                except:
                    pass

            if t_name == type_name:
                target_type = t
                break

        if not target_type:
            try:
                target_type = tmpl.Duplicate(type_name)
            except:
                continue

        # Set Tag on Type as well?
        try:
            p = target_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
            if p: p.Set(TAG_VALUE)
        except:
            pass

        # Build Layers
        try:
            cs = target_type.GetCompoundStructure()
            if not cs:
                cs = CompoundStructure.CreateSingleLayerCompoundStructure(
                    MaterialFunctionAssignment.Structure, 0.1, ElementId.InvalidElementId)

            layers_obj = []
            for layer_def in data["layers"]:
                mat_name = layer_def[0]
                width_ft = m2ft(layer_def[1])
                mat_id = material_cache.get(mat_name, ElementId.InvalidElementId)
                new_layer = CompoundStructureLayer(width_ft, MaterialFunctionAssignment.Structure, mat_id)
                layers_obj.append(new_layer)

            cs.SetLayers(layers_obj)
            target_type.SetCompoundStructure(cs)
        except:
            pass

    # Run the new Opening Logic
    create_opening_types(doc)

    TransactionManager.Instance.TransactionTaskDone()
    print("\nDone. Library v2 (Tagged) Ready.")


build_library()