#! python3
import rhinoscriptsyntax as rs # pyright: ignore[reportMissingImports]
import csv
import os

def import_user_text_from_csv():
    print("--- 📥 INJECTING SPREADSHEET DATA INTO RHINO ---")
    
    # 1. Ask the user to pick the CSV file
    csv_path = rs.OpenFileName("Select your updated CSV file", "CSV Files (*.csv)|*.csv||")
    if not csv_path:
        return print("⚠️ Import cancelled.")

    success_count = 0
    missing_count = 0

    # 2. Open and read the CSV (Using utf-8-sig to handle Excel's encoding perfectly)
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        
        # Validation
        if not header or header[0] != "GUID":
            return print("❌ Error: Invalid CSV. The first column must be 'GUID'.")
            
        # The dynamic keys are everything after "GUID" and "Layer"
        dynamic_keys = header[2:]

        # 3. Process each row
        for row in reader:
            if not row: continue # Skip empty rows
            
            guid = row[0]
            
            # Check if the object still exists in the Rhino model
            if not rs.IsObject(guid):
                missing_count += 1
                continue
                
            # Loop through all the columns for this specific row
            for i, key in enumerate(dynamic_keys):
                # Calculate the column index (offset by 2 for GUID and Layer)
                col_index = i + 2 
                
                # Excel sometimes drops trailing empty cells, so we safely grab the value
                val = row[col_index] if col_index < len(row) else ""
                
                # 4. Inject into Rhino!
                if val == "":
                    # If the Excel cell is empty, delete the key from the Rhino object
                    # to keep the database clean and "sparse"
                    rs.SetUserText(guid, key) 
                else:
                    # Update or Insert the new value
                    rs.SetUserText(guid, key, val)
                    
            success_count += 1

    print(f"\n✅ SUCCESS! Updated attributes for {success_count} objects.")
    if missing_count > 0:
        print(f"⚠️ Skipped {missing_count} rows (objects were deleted from Rhino or invalid GUID).")

if __name__ == "__main__":
    import_user_text_from_csv()