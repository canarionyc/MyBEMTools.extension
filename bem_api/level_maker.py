from Autodesk.Revit.DB import Level
from pyrevit import revit

# 'doc', 'data', and 'result' are injected into this script's memory by startup.py

# 1. Get our array of levels from the incoming Thunder Client payload
levels_data = data.get('levels', []) 
created_count = 0

# 2. Open the pyRevit Context Manager Transaction
with revit.Transaction("BEM: Create Levels"):
    
    for lev in levels_data:
        name = lev.get('name', 'Unnamed Level')
        
        # Ensure the elevation is a float. (Remember: Revit API expects FEET!)
        elevation = float(lev.get('elevation', 0.0))
        
        # Create the level and assign the name
        new_level = Level.Create(doc, elevation) 
        new_level.Name = name
        created_count += 1

# 3. Populate the 'result' dictionary to send back to Thunder Client
result['status'] = 'Success'
result['message'] = 'Created ' + str(created_count) + ' levels.'
result['project'] = data.get('project_name', 'Unknown') 