#! python3
import rhinoscriptsyntax as rs
import json
import os

# --- PATHS ---
MATRIX_PATH = r"C:\dev\MyBEMTools.extension\bem_api\data\layer_matrix.json"

def build_layer_hierarchy():
    if not os.path.exists(MATRIX_PATH):
        print(f"❌ Error: Could not find layer matrix at {MATRIX_PATH}")
        return

    # Load the matrix
    with open(MATRIX_PATH, 'r', encoding='utf-8') as f:
        matrix = json.load(f)

    levels = matrix.get("levels", [])
    categories = matrix.get("categories", [])

    print(f"🏗️ Building Layer Matrix: {len(levels)} Levels x {len(categories)} Categories...")

    # Cross-multiply Levels and Categories
    for level in levels:
        # 1. Create the Parent Layer (Level)
        if not rs.IsLayer(level):
            rs.AddLayer(level)
        
        # 2. Create the Sub-Layers (Categories)
        for cat in categories:
            cat_name = cat.get("name")
            color = cat.get("color", [0, 0, 0])
            
            # In Rhino, nested layers are designated by double colons (::)
            full_layer_path = f"{level}::{cat_name}"
            
            if not rs.IsLayer(full_layer_path):
                rs.AddLayer(full_layer_path, color)

    print("\n✅ SUCCESS! Layer hierarchy generated.")

if __name__ == "__main__":
    build_layer_hierarchy()