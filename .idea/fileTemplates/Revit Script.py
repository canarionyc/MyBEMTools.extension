import sys
from pyrevit import revit

# 1. Acquire Document (Strictly following your script.py structure)
doc = None

# Check if running via CLI (headless)
if '__models__' in globals() and __models__:
    doc = __models__[0] 
# Check if running in UI mode
else:
    try:
        doc = revit.doc
    except Exception:
        pass

if not doc:
    sys.stdout.write("Error: No document acquired. Exiting.\n")
    sys.exit(1)

# 2. UI-Agnostic Output
# Avoid forms.alert() or ProgressBar(). Use sys.stdout.write for universal logging.
sys.stdout.write("Processing model: {}\n".format(doc.Title))
