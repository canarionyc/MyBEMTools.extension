#! python3
import sys
import os
import threading
import importlib

if r'C:\Python312\Lib\site-packages' not in sys.path:
    sys.path.insert(0, r'C:\Python312\Lib\site-packages')

def connect_debugger() -> bool:
    """
    Attempts to connect to PyCharm. 
    Returns True if successful, False if it fails.
    """
    os.environ['PYDEVD_USE_CYTHON'] = 'NO'
    os.environ['PYDEVD_USE_FRAME_EVAL'] = 'NO'
    
    try:
        import pydevd_pycharm
        from _pydevd_bundle.pydevd_additional_thread_info import set_additional_thread_info
        
        current_t = threading.current_thread()
        if not hasattr(current_t, 'additional_info') or current_t.additional_info is None:
            set_additional_thread_info(current_t)
        current_t.name = 'MainThread'
        
        print("Attempting to connect to PyCharm on port 5678...")
        pydevd_pycharm.settrace('localhost', port=5678, suspend=False, patch_multiprocessing=False)
        print("SUCCESS: Connected to PyCharm!")
        return True
        
    except Exception as e:
        print(f"Debugger connection failed: {e}")
        return False

# 1. Boot the debugger and check the result
if not connect_debugger():
    print("--- ABORTING SCRIPT ---")
    sys.exit() # This safely kills the script immediately

# 2. Import your external logic (Execution only reaches here if connected)
from lib import bem_test

# 3. Reload it to ensure latest code
importlib.reload(bem_test)

# 4. Execute the code
bem_test.run_math_loop()