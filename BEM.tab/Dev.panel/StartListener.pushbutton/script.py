from pyrevit import routes
import sys
from io import StringIO

# --- 1. THE HANDLER ---
def code_executor_handler(request):
    # In base.py, the Request object uses .data, not .body
    code = request.data 
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    try:
        exec(code, globals())
        result = redirected_output.getvalue()
        # Response(status, data, headers) from base.py
        return routes.Response(200, result if result else "Success: No output.")
    except Exception as e:
        return routes.Response(500, "Python Error: " + str(e))
    finally:
        sys.stdout = old_stdout

# --- 2. THE RESET ---
print("Resetting Route Server...")
routes.deactivate_server() # __init__.py

# --- 3. THE REGISTRATION ---
# router.py signature: api_name, pattern, method, handler_func
routes.add_route("BEM", "/exec", "POST", code_executor_handler)

# --- 4. START ---
# __init__.py signature: No arguments
# It automatically picks a port starting from user_config.routes_port
active_server = routes.activate_server() 

if active_server:
    print("SUCCESS: Listener is now active on port: {}".format(active_server.port))
else:
    print("FAILED: Could not start server.")

# --- 5. DIAGNOSTICS ---
print("Active Routes for 'BEM':")
# router.py: get_routes(api_name) returns a dict
# The keys are Route namedtuples: ['pattern', 'method']
active_routes_dict = routes.get_routes("BEM")
for route_obj in active_routes_dict.keys():
    print("- Method: {}, Pattern: {}".format(route_obj.method, route_obj.pattern))