#! python3
import rhinoscriptsyntax as rs
import csv
import os

OUTPUT_DIR = r"C:\dev\MyBEMTools.extension\bem_api\output"

def export_user_text_to_csv():
    print("--- 📊 EXPORTING USER TEXT TO SPREADSHEET ---")
    
    # Output path (Desktop)
    # desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    csv_path = os.path.join(OUTPUT_DIR, "Rhino_BEM_Database.csv")

    # 1. Grab all objects in the model
    all_objs = rs.AllObjects()
    if not all_objs: 
        return print("⚠️ No objects found in the model.")

    data_objects = []
    all_keys = set()
    
    # 2. Filter for objects that actually have User Text and collect all unique keys
    for obj in all_objs:
        keys = rs.GetUserText(obj)
        if keys:
            data_objects.append(obj)
            for k in keys:
                all_keys.add(k)
                
    if not data_objects:
        return print("⚠️ No objects with User Text found.")

    # 3. Build the Header Row (Standard ID info + sorted dynamic keys)
    # E.g., ["GUID", "Layer", "family_name", "thickness", ...]
    dynamic_keys = sorted(list(all_keys))
    header = ["GUID", "Layer"] + dynamic_keys

    # 4. Write the CSV
    # Using utf-8-sig so Excel automatically reads Spanish accents correctly!
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for obj in data_objects:
            # Start the row with basic object info
            row = [
                str(obj),
                rs.ObjectLayer(obj)
            ]
            
            # Fetch the value for each column, leave blank if the object doesn't have it
            for key in dynamic_keys:
                val = rs.GetUserText(obj, key)
                row.append(val if val else "")
                
            writer.writerow(row)
            
    print(f"✅ SUCCESS! Exported {len(data_objects)} objects.")
    print(f"File saved to: {csv_path}")
    
    # Auto-open the file in Excel (or your default CSV viewer)
    try:
        os.startfile(csv_path)
    except Exception as e:
        print("Could not auto-open file. You can find it on your Desktop.")

if __name__ == "__main__":
    export_user_text_to_csv()