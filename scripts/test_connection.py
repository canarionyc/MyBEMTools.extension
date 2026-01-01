from pyrevit import revit

doc = revit.doc
print("CONNECTION SUCCESSFUL!")
print("Revit Version: " + doc.Application.VersionName)
print("Current Model: " + doc.Title)