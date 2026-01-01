# -*- coding: utf-8 -*-
import sys
import os
import clr

try:
    clr.AddReference('RevitAPI')
    from Autodesk.Revit.DB import *
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument
    IN_REVIT = True
except ImportError:
    IN_REVIT = False

# ========================================================
# CONFIGURATION
# ========================================================
# EXACT NAME of the schedule in your Project Browser
SCHEDULE_NAME = "Material Takeoff" 

# Output path
user_home = os.environ['USERPROFILE']
desktop = os.path.join(user_home, "Desktop")
OUTPUT_FILENAME = "CTE_Materials_Export.csv"

def export_schedule_to_csv():
    if not IN_REVIT: return

    # 1. Find the Schedule View
    col = FilteredElementCollector(doc).OfClass(ViewSchedule)
    target_view = None
    
    for v in col:
        if v.Name == SCHEDULE_NAME:
            target_view = v
            break
            
    if not target_view:
        print(f"Error: Could not find a schedule named '{SCHEDULE_NAME}'")
        print("Available Schedules:")
        for v in col: print(f" - {v.Name}")
        return

    # 2. Configure Export Options for CSV
    options = ViewScheduleExportOptions()
    options.Title = True                  # Export Header/Title?
    options.ColumnHeaders = FootnoteColumnHeaders.Export # Export Column Names
    options.FieldDelimiter = ","          # COMMA for CSV
    options.TextQualifier = TextQualifier.DoubleQuote
    
    # 3. Export
    # Note: View.Export takes (Folder, Filename, Options)
    try:
        target_view.Export(desktop, OUTPUT_FILENAME, options)
        print(f"Success! Exported to: {os.path.join(desktop, OUTPUT_FILENAME)}")
    except Exception as e:
        print(f"Error exporting: {e}")

export_schedule_to_csv()