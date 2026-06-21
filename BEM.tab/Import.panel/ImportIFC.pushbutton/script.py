#! python3
#%% CELL TITLE: IMPORTS
import clr
import os
from typing import Optional, List as PyList

# Bypass pyrevit.forms and load native Windows Forms for the file picker
clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import OpenFileDialog, DialogResult

from Autodesk.Revit.DB import (
    Transaction, ElementTransformUtils,
    CopyPasteOptions, FilteredElementCollector, BuiltInCategory,
    ElementId, Document
)
from Autodesk.Revit.DB.IFC import IFCImportOptions, IFCImportIntent
from System.Collections.Generic import List

# Access the active Revit application directly
doc = __revit__.ActiveUIDocument.Document
app = __revit__.Application


#%% CELL TITLE: NATIVE FILE PICKER
def pick_ifc_file() -> Optional[str]:
    """Native .NET file picker to avoid pyRevit wrapper crashes in Python 3"""
    dialog: OpenFileDialog = OpenFileDialog()
    dialog.Filter = "IFC Files (*.ifc)|*.ifc"
    dialog.Title = "Select Master IFC Database"
    
    if dialog.ShowDialog() == DialogResult.OK:
        return dialog.FileName
    return None


#%% CELL TITLE: MAIN INJECTION PIPELINE
def direct_ifc_import() -> None:
    print("\n" + "="*80)
    print("INITIALIZING DIRECT NATIVE IFC INJECTION (PURE CPYTHON 3)")
    print("="*80)

    # 1. Target Selection
    ifc_path: Optional[str] = pick_ifc_file()
    if not ifc_path:
        print("[ABORT] No file selected.")
        return

    print("[INFO] Processing database: " + ifc_path)

    # 2. Setup Parametric Translation Engine
    import_opts: IFCImportOptions = IFCImportOptions()
    import_opts.Intent = IFCImportIntent.Parametric 
    
    print("[INFO] Translating IFC database in the background. Please wait...")
    
    # 3. Silent Conversion
    temp_doc: Optional[Document] = app.OpenIFCDocument(ifc_path, import_opts)
    if not temp_doc:
        print("[ERROR] Revit failed to translate the IFC database.")
        return

    # 4. Target Specific Architectural Categories
    categories: PyList[BuiltInCategory] = [
        BuiltInCategory.OST_Levels,  # <-- NEW: Crucial for vertical hosting
        BuiltInCategory.OST_Floors,
        BuiltInCategory.OST_Walls,
        BuiltInCategory.OST_Doors,
        BuiltInCategory.OST_Windows,
        BuiltInCategory.OST_Topography,
        BuiltInCategory.OST_Site
    ]
    
    # PythonNet Fix: Initialize an empty .NET List first
    id_list = List[ElementId]()
    
    for cat in categories:
        collector = FilteredElementCollector(temp_doc).OfCategory(cat).WhereElementIsNotElementType()
        # Add elements directly to the .NET List
        for element in collector:
            id_list.Add(element.Id)

    if id_list.Count == 0:
        temp_doc.Close(False)
        print("[WARNING] No physical elements found to import.")
        return

    # 5. Inject elements directly into active document
    with Transaction(doc, "Direct Native IFC Injection") as t:
        t.Start()
        
        cp_opts: CopyPasteOptions = CopyPasteOptions()
        
        print("[INFO] Injecting " + str(id_list.Count) + " elements...")
        copied_ids = ElementTransformUtils.CopyElements(
            temp_doc, 
            id_list, 
            doc, 
            None, 
            cp_opts
        )
        t.Commit()

    # 6. Memory Cleanup
    temp_doc.Close(False)
    
    print("\n" + "="*80)
    print("[SUCCESS] INJECTION COMPLETE: " + str(copied_ids.Count) + " native elements added.")
    print("="*80 + "\n")


if __name__ == "__main__":
    direct_ifc_import()