#! python3
import sys
import os
import importlib

if r'C:\Python312\Lib\site-packages' not in sys.path:
    sys.path.insert(0, r'C:\Python312\Lib\site-packages')

def connect_vscode() -> bool:
    print("--- Phase 1: VS Code Debugger Initialization ---")
    
    # Silence the harmless Python 3.11+ frozen modules warning
    os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
    
    try:
        import debugpy
        
        # THE FIX: Tell debugpy exactly where the real Python executable is.
        # This prevents it from accidentally launching a second Revit.exe
        debugpy.configure(python=r'C:\Python312\python.exe')
        
        if not debugpy.is_client_connected():
            print("Listening on port 5678...")
            debugpy.listen(('localhost', 5678))
            
            print("Waiting for VS Code to attach... (Press F5 in VS Code now)")
            debugpy.wait_for_client() 
            
        print("SUCCESS: VS Code is connected!")
        return True
        
    except Exception as e:
        print(f"Debugger connection failed: {e}")
        return False

# 1. Connect
if not connect_vscode():
    print("--- ABORTING SCRIPT ---")
    sys.exit()

# 2. Import and reload your external logic
import bem_test
importlib.reload(bem_test)

# 3. Execute
print("--- Phase 2: Handing over to lib/bem_test.py ---")
bem_test.run_math_loop()