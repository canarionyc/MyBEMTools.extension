from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Dimension

# Standard boilerplate to get current document and selection
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
selection = uidoc.Selection.GetElementIds()

if len(selection) == 0:
    print("Please select an element first to see its constraints.")
else:
    # We only check the first item if you selected multiple
    selected_id = selection[0]
    selected_elem = doc.GetElement(selected_id)

    print("--------------------------------------------------")
    print("REPORT: Constraints for '{}' (ID: {})".format(selected_elem.Name, selected_id.IntegerValue))
    print("--------------------------------------------------")

    # 1. Collect all Dimensions (Alignment locks are technically dimensions in Revit API)
    # We search the whole project, not just the view, to be safe.
    all_dims = FilteredElementCollector(doc).OfClass(Dimension).ToElements()

    constraint_count = 0

    for dim in all_dims:
        # We only care if it is LOCKED (The Red Padlock)
        if dim.IsLocked:

            # Get the elements this dimension/constraint connects
            # Note: A constraint might link 2 or more elements
            refs = dim.References
            if not refs:
                continue

            # Check if our selected element is one of the references
            is_connected_to_selection = False
            linked_info = []

            try:
                for ref in refs:
                    linked_id = ref.ElementId

                    # Store the name/ID of everything in this chain
                    if linked_id.IntegerValue != -1:
                        elem = doc.GetElement(linked_id)
                        if elem:
                            name = elem.Name
                            cat = elem.Category.Name if elem.Category else "No Category"
                            linked_info.append("[{}] {} (ID: {})".format(cat, name, linked_id.IntegerValue))

                    # Check if this is the constraint we are looking for
                    if linked_id == selected_id:
                        is_connected_to_selection = True
            except Exception as e:
                # Sometimes references are internal (planes) and fail slightly
                continue

            # If our element was found in this lock, print the whole chain
            if is_connected_to_selection:
                constraint_count += 1
                print("\n[+] Found Lock (ID: {})".format(dim.Id.IntegerValue))
                print("    Linked together:")
                for info in linked_info:
                    # Highlight the other items
                    if str(selected_id.IntegerValue) not in info:
                        print("     -> " + info)
                    else:
                        print("     -> (THIS ELEMENT)")

    if constraint_count == 0:
        print("\nNo locked constraints found for this element.")
    else:
        print("\n--------------------------------------------------")
        print("Found {} active constraints.".format(constraint_count))