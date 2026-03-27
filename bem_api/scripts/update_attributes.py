#! python3
import rhinoscriptsyntax as rs

def sql_update_attributes(target_key,old_value,new_value):
    print("--- STARTING BATCH ATTRIBUTE UPDATE ---")
    
    # ---------------------------------------------------------
    # YOUR "SQL" QUERY PARAMETERS
    # update object_attributes set key = new_value where key = old_value
    # ---------------------------------------------------------
    

    
    # Grab literally every object in the Rhino document
    all_objects = rs.AllObjects()
    if not all_objects:
        print("No objects found in the model.")
        return
        
    update_count = 0
    
    # Iterate through them like rows in a database
    for obj in all_objects:
        # Check if the object has this specific key
        current_val = rs.GetUserText(obj, target_key)
        
        # If the value matches our 'WHERE' clause
        if current_val == old_value:
            # Apply the 'SET' clause
            rs.SetUserText(obj, target_key, new_value)
            update_count += 1
            
    if update_count > 0:
        print(f"✅ SUCCESS: Updated {update_count} objects!")
        print(f"   Changed '{target_key}' from '{old_value}' -> '{new_value}'")
    else:
        print(f"⚠️ No objects found where {target_key} = '{old_value}'.")

if __name__ == "__main__":
    target_key = "family_name" 
    old_value='Wall_Interior'
    new_value='Tabique - 10 cm'
    sql_update_attributes(target_key, old_value,new_value)