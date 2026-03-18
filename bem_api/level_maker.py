from Autodesk.Revit.DB import Level, UnitUtils, UnitTypeId
from pyrevit import revit

levels_data = data.get('levels', [])
created_count = 0

with revit.Transaction("BEM: Create Metric Levels"):
    
    for lev in levels_data:
        name = lev.get('name', 'Unnamed Level')
        
        # 1. Grab the metric elevation from your payload (e.g., 3.0 meters)
        elevation_m = float(lev.get('elevation', 0.0))
        
        # 2. Convert Meters to Internal Units (Feet) using Revit 2025 syntax
        elevation_internal = UnitUtils.ConvertToInternalUnits(elevation_m, UnitTypeId.Meters)
        
        # 3. Feed the internal feet value to the API
        new_level = Level.Create(doc, elevation_internal)
        new_level.Name = name
        created_count += 1

result['status'] = 'Success'
result['message'] = 'Created {} metric levels.'.format(created_count)
result['project'] = doc.Title