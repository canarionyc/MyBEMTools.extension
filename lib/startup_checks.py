

def check_data_libraries() -> bool:
    print(">>> CHECK 4: Data Libraries")
    import os
    import locale
    
    # --- THE LOCALE SANITIZER ---
    # Temporarily remove ISO language codes that confuse the Windows C-runtime
    env_vars_to_scrub = ['LANG', 'LANGUAGE', 'LC_ALL', 'LC_CTYPE']
    scrubbed_values = {}
    
    for var in env_vars_to_scrub:
        if var in os.environ:
            scrubbed_values[var] = os.environ[var]
            del os.environ[var]
            
    try:
        # Force Python to adopt the native Windows system locale
        locale.setlocale(locale.LC_ALL, '')
    except Exception:
        pass

    # --- IMPORT PANDAS ---
    try:
        import pandas as pd
        import numpy as np
        print("    [SUCCESS] Pandas and Numpy imported successfully.")
        success = True
    except Exception as e:
        print(f"    [ERROR] Failed to import data libraries: {e}")
        success = False
        
    # Restore the environment variables so we don't mess up Revit
    for var, val in scrubbed_values.items():
        os.environ[var] = val
        
    return success