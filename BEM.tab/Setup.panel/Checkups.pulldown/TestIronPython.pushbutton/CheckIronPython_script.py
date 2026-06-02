# -*- coding: utf-8 -*-
import sys
import os
import clr
from pyrevit import script, revit, DB

output = script.get_output()
output.print_md("# 🏥 BEM SYSTEM DIAGNOSTIC (Windows 10)")


def check_environment():
    all_green = True

    # --- 2. REVIT VERSION CHECK ---
    print("\n>>> CHECK 2: Revit Version")
    try:
        app = __revit__.Application
        name = app.VersionName
        build = app.VersionBuild
        print("    [INFO] Name:  {}".format(name))
        print("    [INFO] Build: {}".format(build))
    except Exception as e:
        print("    [❌ ERROR] Could not access Revit App: {}".format(e))

    # --- 3. PATH HYGIENE (CRITICAL) ---
    print("\n>>> CHECK 3: System Path Hygiene")
    print("    [INFO] Scanning sys.path for rogue libraries...")
    print("    [INFO] Current sys.path entries:")
    for p in sys.path:
        print("    [INFO] - {}".format(p))
    dirty_paths = []
    for p in sys.path:
        # We look for hardcoded external Python paths (like Anaconda or C:\Python312)
        # that shouldn't be here in IronPython
        if "Python3" in p or "site-packages" in p:
            # Filter out pyRevit's own site-packages which are fine
            if "pyRevit" not in p:
                print("    [⚠️ DETECTED] External Path: {}".format(p))
                dirty_paths.append(p)

    if not dirty_paths:
        print("    [✅ SUCCESS] System path is clean.")
    else:
        print("    [❌ WARNING] Found {} external paths.".format(len(dirty_paths)))
        # This is often acceptable in IronPython as it ignores CPython DLLs, but good to know.

    # --- 4. DATABASE CAPABILITY ---
    print("\n>>> CHECK 4: SQLite Availability")
    try:
        import sqlite3
        print("    [❌ WARNING] sqlite3 module found (Unexpected for IronPython).")
        print("    [INFO] Location: {}".format(sqlite3.__file__))
    except ImportError:
        print("    [✅ SUCCESS] sqlite3 module NOT found (Expected).")
        print("    [INFO] This confirms we are strictly in the .NET CLR environment.")

    # --- 5. PYREVIT CORE CHECK ---
    print("\n>>> CHECK 5: pyRevit Core")
    try:
        from pyrevit import coreutils
        print("    [✅ SUCCESS] pyRevit Core loaded successfully.")
    except Exception as e:
        print("    [❌ CRITICAL] pyRevit Core failed to load: {}".format(e))
        all_green = False

    # --- SUMMARY ---
    print("\n" + "=" * 40)
    if all_green:
        output.print_md("## ✅ DIAGNOSTIC RESULT: ALL GREEN")
        print("System is ready for the 'Decoupled' Architecture.")
    else:
        output.print_md("## ⚠️ DIAGNOSTIC RESULT: CHECK WARNINGS")


if __name__ == "__main__":
    # --- 1. PYTHON ENGINE CHECK ---
    print("\n>>> CHECK 1: Python Engine")
    engine = sys.version
    print("    [INFO] Engine: {}".format(engine))

    # Check for IronPython specifically
    if "IronPython" in engine:
        print("    [✅ SUCCESS] Running in IronPython (Stable Mode).")
    else:
        print("    [❌ WARNING] Running in CPython.")
        all_green = False

    check_environment()