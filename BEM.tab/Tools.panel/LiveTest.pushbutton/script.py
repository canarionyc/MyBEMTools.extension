# -*- coding: utf-8 -*-
from pyrevit import forms
from Autodesk.Revit.DB import *

# This is the pyRevit shortcut to get the document
doc = __revit__.ActiveUIDocument.Document

# 1. Grab Project Info
project_name = doc.ProjectInformation.Name
version = __revit__.Application.VersionName

# 2. Pop up a message box in Revit
message = "BRIDGE ACTIVE!\n\nProject: {}\nRevit Version: {}".format(project_name, version)
forms.alert(message, title="BEM Live Route")

# 3. Add a simple BEM check
units = doc.GetUnits().GetFormatOptions(SpecTypeId.Length).GetUnitTypeId()
print("Current Project Units: {}".format(units))
