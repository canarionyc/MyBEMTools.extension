import clr
import csv
import os
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import Level, UnitUtils, UnitTypeId
from pyrevit import revit

# The listener automatically provides 'data', 'doc', and 'result'
csv_path = data.get('csv_path', '')
created_count = 0

# 1. Validation: Check if the CSV file actually exists
if not os.path.exists(csv_path):
    result['status'] = 'Error'
    result['message'] = 'CSV file not found at: {}'.format(csv_path)
else:
    with revit.Transaction("BEM: Create Metric Levels from CSV"):
        
        # 2. Open and read the CSV file
        with open(csv_path, 'r') as csv_file:
            # DictReader automatically uses the first row (Name,Elevation) as keys
            csv_reader = csv.DictReader(csv_file)
            
            for row in csv_reader:
                # Grab exact name and elevation from the CSV row
                level_name = row.get('Name', 'Unnamed Level')
                elevation_m = float(row.get('Elevation', 0.0))
                
                # Convert Meters to Internal Units (Feet) using Revit 2025 syntax
                elevation_internal = UnitUtils.ConvertToInternalUnits(elevation_m, UnitTypeId.Meters)
                
                # Feed the internal feet value to the API
                new_level = Level.Create(doc, elevation_internal)
                new_level.Name = level_name
                created_count += 1

    # 3. Send successful response back to your terminal
    result['status'] = 'Success'
    result['message'] = 'Created {} metric levels from CSV.'.format(created_count)
    result['project'] = doc.Title