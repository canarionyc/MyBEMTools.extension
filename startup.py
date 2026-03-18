from pyrevit import routes, revit
from Autodesk.Revit.DB import FilteredElementCollector, Wall, Floor

# 1. Initialize the pyRevit Routes API
api = routes.API("bem_api")

# 2. Define the endpoint to listen for POST requests
@api.route("/process", methods=["POST"])
def process_payload(request):
    try:
        # The 'request.data' object contains your parsed JSON payload from PowerShell
        payload = request.data if request.data else {}
        client_msg = payload.get("message", "No message provided")
        
        # Grab the active Revit document (pyRevit Routes handles the API context safely!)
        doc = revit.doc
        if not doc:
            return routes.make_response(data={"status": "error", "message": "No active Revit model."})
            
        # Do your Revit data extraction
        walls = FilteredElementCollector(doc).OfClass(Wall).GetElementCount()
        floors = FilteredElementCollector(doc).OfClass(Floor).GetElementCount()
        
        # pyRevit Routes automatically converts Python dictionaries into JSON responses
        result = {
            "status": "success",
            "model": doc.Title,
            "data": {"walls": walls, "floors": floors},
            "client_msg": client_msg
        }
        
        return result

    except Exception as e:
        return routes.make_response(data={"status": "fatal_error", "details": str(e)})