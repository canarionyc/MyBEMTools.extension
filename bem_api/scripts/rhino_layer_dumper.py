#! python3
import rhinoscriptsyntax as rs
import json
import os

# --- PATHS ---
OUTPUT_DIR = r"C:\dev\MyBEMTools.extension\bem_api\output"
PAYLOAD_PATH = os.path.join(OUTPUT_DIR, "payload.json")
RULES_PATH = r"C:\dev\MyBEMTools.extension\bem_api\data\rules.json"
CATALOG_PATH = r"C:\dev\MyBEMTools.extension\bem_api\data\catalog.json" # NEW

def resolve_family_and_thickness(target_name, catalog):
    """Searches the catalog for a family name and returns (exact_name, thickness_mm)."""
    if not target_name: return None, None
    for bim_category, families in catalog.items():
        if target_name in families:
            # Found it! Convert meters from JSON to millimeters for Rhino/Payload
            thick_mm = families[target_name]["total_thickness_m"] * 1000.0
            return target_name, thick_mm
    return None, None

def dump_bem_geometry():
    print("--- STARTING STRICT BEM DUMP ---")
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

    # 1. Load Rules and Catalog
    with open(RULES_PATH, 'r', encoding='utf-8-sig') as f:
        master_data = json.load(f)
    schema_keys = master_data.get("schema", {}).keys()
    
    with open(CATALOG_PATH, 'r', encoding='utf-8-sig') as f:
        catalog_data = json.load(f)

    curves = rs.ObjectsByType(rs.filter.curve)
    if not curves: return print("⚠️ No lines or polylines found.")

    payload = {}
    stats = {"Lines": 0, "Polylines": 0, "Skipped": 0, "Warnings": 0}

    # 2. Process each curve
    for crv in curves:
        full_layer = rs.ObjectLayer(crv)
        layer_parts = full_layer.split("::")
        if len(layer_parts) < 2 or not layer_parts[0].startswith("LVL"): continue

        parent_level = layer_parts[0]
        category = layer_parts[1]
        rule_data = master_data.get("types", {}).get(category, {})

        geom_type = "Line" if rs.IsLine(crv) else "Polyline"
        coords = [list(pt)[:2] for pt in rs.CurvePoints(crv)]

        element_data = {
            "level": parent_level,
            "category": category,
            "geometry_type": geom_type,
            "coordinates": coords
        }

        # User Text Extraction
        user_keys = rs.GetUserText(crv)
        if user_keys:
            for key in user_keys:
                clean_key = key.lower()
                if clean_key in schema_keys:
                    raw_val = rs.GetUserText(crv, key)
                    try: element_data[clean_key] = float(raw_val)
                    except ValueError: element_data[clean_key] = raw_val

        # --- THE FAIL-SAFE CATALOG LOOKUP ---
        user_fam = element_data.get("family_name")
        rule_fam = rule_data.get("family_name")
        final_fam, thickness = None, None

        # Try User Text first
        if user_fam:
            final_fam, thickness = resolve_family_and_thickness(user_fam, catalog_data)
            if not final_fam:
                print(f"  ⚠️ Warning: UserText family '{user_fam}' is misspelled or missing in Catalog! Falling back to Rule Default.")
                stats["Warnings"] += 1

        # Fallback to Rule Default if User Text failed or was empty
        if not final_fam and rule_fam:
            final_fam, thickness = resolve_family_and_thickness(rule_fam, catalog_data)

        # Apply strictly validated data
        if final_fam and thickness:
            element_data["family_name"] = final_fam
            element_data["thickness"] = thickness
        else:
            print(f"  ❌ FATAL ERROR: No valid family found for {category} on {parent_level}. Skipping curve.")
            stats["Skipped"] += 1
            continue

        if geom_type == "Line": stats["Lines"] += 1
        else: stats["Polylines"] += 1

        if parent_level not in payload: payload[parent_level] = []
        payload[parent_level].append(element_data)

    # 4. Export
    if payload:
        with open(PAYLOAD_PATH, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
        print(f"\n✅ SUCCESS! Dumped {sum(len(v) for v in payload.values())} elements to payload.")
        if stats["Warnings"] > 0 or stats["Skipped"] > 0:
            print(f"⚠️ {stats['Warnings']} Warnings, {stats['Skipped']} Skipped curves.")
    else:
        print("\n⚠️ No valid geometry found to export.")

if __name__ == "__main__":
    dump_bem_geometry()