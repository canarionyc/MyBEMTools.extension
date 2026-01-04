# -*- coding: utf-8 -*-
from pyrevit import script, HOST_APP
import os

output = script.get_output()

print("## PYREVIT ENVIRONMENT DIAGNOSTICS ##")
print("pyRevit Version: {}".format(HOST_APP.version))

# -*- coding: utf-8 -*-
from pyrevit import script, HOST_APP
import os

output = script.get_output()
output.print_md("### Checking for Python Runtime Conflicts")

try:
    from System import AppDomain
    assemblies = AppDomain.CurrentDomain.GetAssemblies()
    # Look for the Python.Runtime DLL used by pythonnet
    py_runtimes = [a for a in assemblies if "Python.Runtime" in a.FullName]
    
    if py_runtimes:
        print("[!] CONFLICT: Python.Runtime is already loaded by another add-in.")
        for a in py_runtimes:
            print("- Loaded From: {}".format(a.Location))
            print("- Full Name: {}".format(a.FullName))
        output.print_md("**Recommendation:** Identify the add-in in the path above. "
                        "Try disabling it to see if pyRevit CPython starts working.")
    else:
        print("[OK] No competing Python runtimes detected in this session.")
except Exception as e:
    print("Error checking assemblies: {}".format(e))

print("\nSystem Executable: {}".format(os.sys.executable))


# Check CPython Config
try:
    from pyrevit.loader import sessioninfo
    engine_cfg = sessioninfo.get_session_info().engine_configs
    cpython_cfg = [e for e in engine_cfg if "cpython" in e.engine_id.lower()]
    if cpython_cfg:
        print("\n[CPython Config Found]")
        print("- Engine Path: {}".format(cpython_cfg[0].engine_path))
    else:
        print("\n[!] No CPython engine configured in pyRevit settings.")
except Exception as e:
    print("Could not retrieve engine config: {}".format(e))

print("\n## OS ENVIRONMENT VARIABLES ##")
print("PYTHONPATH: {}".format(os.environ.get('PYTHONPATH', 'NOT SET')))
print("PYTHONHOME: {}".format(os.environ.get('PYTHONHOME', 'NOT SET')))



##############################################################

from pyrevit import MISC_LIB_DIR, MAIN_LIB_DIR
from pyrevit import coreutils
from pyrevit import framework
from pyrevit import script

# FIX 1: Reference the specific assembly name used in Revit 2025 / .NET 8
try:
    framework.clr.AddReference('pyRevitLabs.IronPython')
except Exception:
    # Fallback for older versions or custom clones
    framework.clr.AddReference('IronPython')

import IronPython.Hosting
import IronPython.Runtime

__context__ = 'zero-doc'
output = script.get_output()

# Configuration
TEST_UNIT = 100
MAX_TESTS = 5 * TEST_UNIT
test_code = "import sys; sys.path.append('test_path')"


def run_test(engine, runtime):
    """Executes code in a fresh scope."""
    scope = runtime.CreateScope()
    source = engine.CreateScriptSourceFromString(test_code)
    comped = source.Compile()
    comped.Execute(scope)


def make_engine():
    """Creates a new IronPython engine with .NET 8 compatible options."""
    options = {"Frames": True, "FullFrames": True}
    # Using the hosting API to create the engine
    engine = IronPython.Hosting.Python.CreateEngine(options)

    # Ensure the engine can find pyRevit libraries
    engine.SetSearchPaths(framework.List[str]([MISC_LIB_DIR, MAIN_LIB_DIR]))

    runtime = engine.Runtime
    return engine, runtime


engine_times = []
output_times = []

# Execution Loop
for idx in range(1, MAX_TESTS + 1):
    try:
        engine_timer = coreutils.Timer()

        # Initialize and Run
        engine, runtime = make_engine()
        run_test(engine, runtime)

        # Cleanup
        runtime.Shutdown()

        eng_time = engine_timer.get_time()
        engine_times.append(eng_time)

        # Track output overhead
        output_timer = coreutils.Timer()
        # print('Engine {}: {}ms'.format(idx, int(eng_time * 1000)))
        output_times.append(output_timer.get_time())

    except Exception as e:
        print('FAILED at Engine {}: {}'.format(idx, str(e)))
        break

# Charting Results
chart = output.make_line_chart()
chart.data.labels = [x for x in range(1, len(engine_times) + 1)]

engine_dataset = chart.data.new_dataset('Engine Init + Run (s)')
engine_dataset.set_color(0xc3, 0x10, 0x10, 0.4)
engine_dataset.data = engine_times

chart.draw()