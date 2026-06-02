#! python3
#%% SETUP AND IMPORTS
import sys
import os
import sqlite3

from typing import List, Tuple, Any

#%% startup_checks.py will be imported and reloaded to ensure we have the latest version of the code in this live environment.
import importlib

# 1. Standard import (Python will use the cache if it exists)
import startup_checks

# 2. Force the reload (Python throws away the cache and reads your latest save)
importlib.reload(startup_checks)

#%% PATH MANAGEMENT
original_path: List[str] = list(sys.path)
injected_paths: List[str] = []

def inject_path(path_str: str) -> None:
    """Injects a path into sys.path safely."""
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
        injected_paths.append(path_str)

# Inject standard external CPython paths
inject_path(r'C:\Python312\Lib\site-packages')
inject_path(r'C:\Python312\Lib')

#%% SYSTEM CHECKS
def check_python_engine() -> bool:
    print(">>> CHECK 1: Python Engine")
    print(f"    [INFO] Engine: {sys.version}")
    return True

def check_revit_version() -> bool:
    print(">>> CHECK 2: Revit Version")
    try:
        app = __revit__.Application
        print(f"    [INFO] Name:  {app.VersionName}")
        print(f"    [INFO] Build: {app.VersionBuild}")
        return True
    except Exception as e:
        print(f"    [ERROR] Could not access Revit App: {e}")
        return False

def check_debugger() -> bool:
    print(">>> CHECK 3: Debugger Availability")
    try:
        import pydevd_pycharm
        print("    [SUCCESS] pydevd_pycharm is installed and ready.")
        print(f"    [INFO] Location: {pydevd_pycharm.__file__}")
        return True
    except ImportError:
        print("    [WARNING] pydevd_pycharm not found. Step-through debugging disabled.")
        return False




def check_sqlite_database(db_path: str) -> bool:
    print(">>> CHECK 5: SQLite Database")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, material_group FROM materials LIMIT 5")
            rows: List[Tuple[Any, ...]] = cursor.fetchall()
            
            print(f"    [SUCCESS] Connected to: {os.path.basename(db_path)}")
            print("    [INFO] Sample Materials:")
            for row in rows:
                print(f"      - {row[0]} ({row[1]})")
            conn.close()
            return True
        except Exception as e:
            print(f"    [ERROR] SQLite query failed: {e}")
            return False
    else:
        print(f"    [WARNING] SQLite DB not found at {db_path}")
        return False

#%% CLEANUP
def cleanup_environment() -> None:
    """
    Cleans up injected sys paths. 
    Crucially, it does NOT touch sys.modules to avoid C-extension reload crashes.
    """
    print("--- CLEANING ENVIRONMENT ---")
    for path in injected_paths:
        if path in sys.path:
            sys.path.remove(path)

#%% DEMONSTRATION
if __name__ == "__main__":
    print("# BEM SYSTEM DIAGNOSTIC")
    
    results: List[bool] = [
        check_python_engine(),
        check_revit_version(),
        check_debugger(),
        startup_checks.check_data_libraries(),
        check_sqlite_database(r'C:/ProyectosCTEyCEE/CTEHE2019/Proyectos/EjemploI_2526_Option1_Config1/output/hulc_data.sqlite')
    ]
    
    cleanup_environment()
    
    print("=" * 40)
    if all(results):
        print("## DIAGNOSTIC RESULT: ALL GREEN")
    else:
        print("## DIAGNOSTIC RESULT: CHECK WARNINGS")