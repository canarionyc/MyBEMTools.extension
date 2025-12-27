import sys
# No imports from your custom libs yet
print("--- TEST START ---")
try:
    from Autodesk.Revit.DB import *
    print("Revit API Loaded")
    if '__models__' in globals():
        print("Models found: " + str(__models__))
except Exception as e:
    print("Error: " + str(e))
print("--- TEST END ---")