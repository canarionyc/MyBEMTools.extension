import sys
import os
import clr
import json

# Standard setup
lib_path = r"C:\repos\pyRevit-Master\bin\engines\IPY342\lib"
if lib_path not in sys.path:
    sys.path.append(lib_path)

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

output_file = r"C:\Users\Public\pyrevit_headless_debug.txt"

try:
    # READ THE TUNNEL: Get the path directly from the OS environment
    target_file = os.environ.get('MY_AUDIT_MODEL')
    
    if not target_file:
        raise Exception("Tunnel Failed: MY_AUDIT_MODEL environment variable not found.")

    app = __revit__.Application
    
    # SILENT OPEN (The bypass we perfected earlier)
    options = OpenOptions()
    options.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets
    options.Audit = True 
    
    m_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(target_file)
    doc = app.OpenDocumentFile(m_path, options)

    if doc:
        wall_count = FilteredElementCollector(doc).OfClass(Wall).GetElementCount()
        result = {
            "status": "success",
            "model": doc.Title,
            "path_used": target_file,
            "wall_count": wall_count
        }
        doc.Close(False)
    else:
        result = {"status": "error", "message": "Revit DB engine failed to load the file."}

    with open(output_file, "w") as f:
        f.write(json.dumps(result, indent=4))

except Exception as e:
    with open(output_file, "w") as f:
        f.write(json.dumps({"error": str(e)}, indent=4))
