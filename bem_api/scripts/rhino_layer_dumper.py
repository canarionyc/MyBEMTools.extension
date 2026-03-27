#! python3
import rhinoscriptsyntax as rs
import json
import os

# --- PATHS ---
OUTPUT_DIR = r"C:\dev\MyBEMTools.extension\bem_api\output"
PAYLOAD_PATH = os.path.join(OUTPUT_DIR, "payload.json")
RULES_PATH = r"C:\dev\MyBEMTools.extension\bem_api\data\rules.json"

def dump_bem_geometry():
    print("--- STARTING STRICT BEM DUMP ---")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Load the official schema from rules.json
    if not os.path.exists(RULES_PATH):
        print("❌ Error: Cannot find rules.json to load schema!")
        return

    with open(RULES_PATH, 'r', encoding='utf-8') as f:
        master_data = json.load(f)
        
    schema_keys = master_data.get("schema", {}).keys()

    curves = rs.ObjectsByType(rs.filter.curve)
    if not curves:
        print("⚠️ No lines or polylines found.")
        return

    payload_data = []
    stats = {"Lines": 0, "Polylines": 0, "Skipped": 0, "Warnings": 0}

    # 2. Process each curve
    for crv in curves:
        full_layer = rs.ObjectLayer(crv)
        layer_parts = full_layer.split("::")
        
        if len(layer_parts) < 2 or not layer_parts[0].startswith("LVL") or not layer_parts[-1].startswith("BEM"):
            stats["Skipped"] += 1
            continue
            
        parent_level = layer_parts[0]
        category = layer_parts[-1]
        
        pts = rs.CurvePoints(crv)
        if not pts: continue
            
        geo_type = "Line" if len(pts) == 2 else "Polyline"
        stats[geo_type + "s"] += 1
        
        element_data = {
            "level": parent_level,
            "category": category,
            "geometry_type": geo_type,
            "coordinates": [[round(pt.X, 4), round(pt.Y, 4)] for pt in pts]
        }
        
        # 3. Dynamic Attribute Extraction & Validation
        user_keys = rs.GetUserText(crv)
        if user_keys:
            for key in user_keys:
                clean_key = key.lower() # Force lowercase to match snake_case standard
                
                if clean_key in schema_keys:
                    raw_val = rs.GetUserText(crv, key)
                    # Try to convert numbers to floats so the JSON is clean, otherwise keep as string
                    try:
                        element_data[clean_key] = float(raw_val)
                    except ValueError:
                        element_data[clean_key] = raw_val
                else:
                    print(f"   ⚠️ Warning: Ignored invalid attribute '{key}' on {category} wall.")
                    stats["Warnings"] += 1

        payload_data.append(element_data)

    # 4. Export
    if payload_data:
        with open(PAYLOAD_PATH, 'w', encoding='utf-8') as f:
            json.dump(payload_data, f, indent=4, ensure_ascii=False)
            
        print(f"\n✅ SUCCESS! Dumped {len(payload_data)} elements to: payload.json")
        print(f"Stats: {stats['Lines']} Lines, {stats['Polylines']} Polylines.")
        if stats["Warnings"] > 0:
            print(f"⚠️ Generated {stats['Warnings']} warnings for invalid attributes. Check command history.")
    else:
        print("\n⚠️ No valid geometry found to export.")

if __name__ == "__main__":
    dump_bem_geometry()