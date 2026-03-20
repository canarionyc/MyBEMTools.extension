
#%% setup
import sys
import os
import threading
import logging
from pyrevit import routes
#%% Revit-specific imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import IExternalEventHandler, ExternalEvent

#%% --- SET UP LOGGING (IP27 & APPDATA Compatible) ---
appdata = os.environ.get('APPDATA', '')
default_log_dir = os.path.join(appdata, 'BEM_API')
log_dir = os.environ.get('BEM_API_LOGDIR', default_log_dir)

# Create the directory if it does not exist
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_path = os.path.join(log_dir, 'bem_api.log')

logging.basicConfig(
    filename=log_path, 
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
#%% --- MAIN THREAD EXECUTOR CLASS ---
class MainThreadExecutor(IExternalEventHandler):
    def __init__(self):
        self.script_string = ""
        self.local_env = {}
        self.error = None
        self.finished = threading.Event()

    def Execute(self, uiapp):
        try:
            self.local_env["uiapp"] = uiapp
            self.local_env["uidoc"] = uiapp.ActiveUIDocument
            self.local_env["doc"] = uiapp.ActiveUIDocument.Document
            exec(self.script_string, globals(), self.local_env)
        except Exception as e:
            self.error = str(e)
        finally:
            self.finished.set()

    def GetName(self):
        return "PyRevit Routes Main Thread Executor"

executor_handler = MainThreadExecutor()
executor_event = ExternalEvent.Create(executor_handler)
execute_lock = threading.Lock()

api = routes.API("bem_api")

@api.route('/execute', methods=['POST'])
def execute_external_script(request):
    payload = request.data if request.data else {}
    
    # Log the incoming request (Using IP27 formatting)
    logging.info("REQUEST RECEIVED: {}".format(payload))
    
    script_path = payload.get("script_path", "")
    input_data = payload.get("data", {})

    if not script_path or not os.path.isfile(script_path):
        err_msg = "Could not find file: {}".format(script_path)
        logging.error(err_msg)
        return {"status": "error", "message": err_msg}

    try:
        with open(script_path, 'r') as file:
            script_string = file.read()
    except Exception as e:
        err_msg = "Failed to read file: {}".format(e)
        logging.error(err_msg)
        return {"status": "error", "message": err_msg}

    with execute_lock:
        local_env = {
            "data": input_data,
            "result": {}
        }
        
        executor_handler.script_string = script_string
        executor_handler.local_env = local_env
        executor_handler.error = None
        executor_handler.finished.clear()
        
        executor_event.Raise()
        success = executor_handler.finished.wait(timeout=30)
        
        if not success:
            err_msg = "Execution timed out. Main thread blocked."
            logging.error(err_msg)
            return {"status": "error", "details": err_msg}
            
        if executor_handler.error:
            logging.error("SCRIPT ERROR: {}".format(executor_handler.error))
            return {"status": "error", "details": executor_handler.error}
            
        final_result = executor_handler.local_env.get("result")
        logging.info("SUCCESS: {}".format(final_result))
        return {"status": "success", "result": final_result}