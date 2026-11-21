# -*- coding: utf-8 -*-
#%% IMPORTS
import os
import csv
from typing import List, Tuple
from pyrevit import forms

#%% TYPE CATALOG PARSER
def parse_type_catalog(txt_path: str) -> List[str]:
    """Reads a Revit type catalog and extracts the type names."""
    type_names = [] # type: List[str]
    try:
        with open(txt_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                # Skip header line which usually starts with a comma or has column definitions
                if not line.strip() or line.startswith(','):
                    continue
                # The first column before the comma is the type name
                parts = line.split(',')
                if parts:
                    type_names.append(parts[0].strip())
    except Exception as e:
        print("Error reading type catalog: " + str(e))
    return type_names

#%% RFA BACKGROUND EXTRACTOR
def extract_types_from_rfa(rfa_path: str) -> List[str]:
    """Opens RFA in the background to read embedded family types."""
    type_names = [] # type: List[str]
    app = __revit__.Application
    try:
        # Open document in background (does not add to current project)
        fam_doc = app.OpenDocumentFile(rfa_path)
        if fam_doc.IsFamilyDocument:
            for fam_type in fam_doc.FamilyManager.Types:
                type_names.append(fam_type.Name)
        fam_doc.Close(False)
    except Exception as e:
        print("Error opening RFA: " + str(e))
    return type_names

#%% MAIN EXECUTION
def main() -> None:
    # Prompt user to select the library folder
    folder_path = forms.select_folder()
    if not folder_path:
        return

    output_data = [] # type: List[Tuple[str, str, str]]
    output_data.append(("Family Name", "Type Name", "Source"))

    # Find all RFA files in the selected directory
    rfa_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".rfa")]
    
    if not rfa_files:
        print("No RFA files found in the selected folder.")
        return

    # Process files with a progress bar
    with forms.ProgressBar(title="Analyzing Families...") as pb:
        for idx, rfa_file in enumerate(rfa_files):
            rfa_path = os.path.join(folder_path, rfa_file)
            txt_path = rfa_path[:-4] + ".txt"
            family_name = rfa_file[:-4]

            # Fast method: Read the TXT catalog if it exists
            if os.path.exists(txt_path):
                types = parse_type_catalog(txt_path)
                source = "Type Catalog (TXT)"
            # Slow method: Open the family in the background if no catalog exists
            else:
                types = extract_types_from_rfa(rfa_path)
                source = "Embedded (RFA)"

            # Append results to our list
            if not types:
                output_data.append((family_name, "No Types Found", source))
            else:
                for t in types:
                    output_data.append((family_name, t, source))

            pb.update_progress(idx + 1, len(rfa_files))

    # Prompt user to save the CSV file
    save_path = forms.save_file(file_ext='csv', default_name='Family_Catalog.csv')
    if save_path:
        with open(save_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(output_data)
        print("Export successful. You can open this CSV file directly in Excel: " + save_path)

if __name__ == "__main__":
    main()