from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Dimension, ElementId

# ---------------- CONFIGURATION ----------------
# Set to True to see what your neighbors are locked to as well (the "Web")
# Set to False to see only direct locks to your selection
RECURSIVE_DEPTH = True
# -----------------------------------------------

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
selection_ids = uidoc.Selection.GetElementIds()


# Helper to format nodes for Mermaid (removes special chars)
def clean_name(elem):
    if not elem: return "Unknown"
    # Create a safe ID string like "Wall_12345"
    safe_id = "{}_{}".format(elem.Category.Name if elem.Category else "Element", elem.Id.IntegerValue)
    safe_id = safe_id.replace(" ", "")
    # Create a readable label like "Basic Wall [12345]"
    label = "{} [{}]".format(elem.Name, elem.Id.IntegerValue)
    return safe_id, label


# Set of processed connections to avoid duplicates
connections = set()
nodes_def = {}  # Store node definitions to print them uniquely later


def get_constraints(target_ids):
    # Get all locked dimensions in the project
    all_dims = FilteredElementCollector(doc).OfClass(Dimension).ToElements()

    found_neighbors = []

    for dim in all_dims:
        if dim.IsLocked and dim.References:
            try:
                # Get all element IDs involved in this single lock
                linked_ids = []
                for ref in dim.References:
                    if ref.ElementId != ElementId.InvalidElementId:
                        linked_ids.append(ref.ElementId)

                # Check if this lock involves any of our target elements
                # Intersection logic: if any target_id is in linked_ids
                if not set(target_ids).intersection(set(linked_ids)):
                    continue

                # Create graph edges between all elements in this lock
                # Usually a lock is just 2 items, but could be a chain
                for i in range(len(linked_ids)):
                    for j in range(i + 1, len(linked_ids)):
                        id1 = linked_ids[i]
                        id2 = linked_ids[j]

                        elem1 = doc.GetElement(id1)
                        elem2 = doc.GetElement(id2)

                        if elem1 and elem2:
                            id1_safe, label1 = clean_name(elem1)
                            id2_safe, label2 = clean_name(elem2)

                            # Store Node Definitions
                            nodes_def[id1_safe] = '{}(["{}"])'.format(id1_safe, label1)
                            nodes_def[id2_safe] = '{}(["{}"])'.format(id2_safe, label2)

                            # Create Edge (Using --- for mutual constraint)
                            # Sort to ensure A---B and B---A are treated as same
                            edge = tuple(sorted([id1_safe, id2_safe]))
                            if edge not in connections:
                                connections.add(edge)
                                # Add to neighbors list for recursion
                                if id1 in target_ids: found_neighbors.append(id2)
                                if id2 in target_ids: found_neighbors.append(id1)

            except Exception as e:
                continue

    return found_neighbors


if not selection_ids:
    print("Please select an element first.")
else:
    print("Graphing constraints...")

    # Pass 1: Direct Constraints
    neighbors = get_constraints(selection_ids)

    # Pass 2: Recursive (Network)
    if RECURSIVE_DEPTH and neighbors:
        get_constraints(neighbors)

    # ---------------- OUTPUT MERMAID ----------------
    print("\nCopy the code below into https://mermaid.live/ \n")
    print("graph TD")

    # Print Nodes
    for key, val in nodes_def.items():
        print("    " + val)

    # Print Styles (Optional: Highlight the selection)
    for sel_id in selection_ids:
        elem = doc.GetElement(sel_id)
        if elem:
            s_id, _ = clean_name(elem)
            print("    style {} fill:#f96,stroke:#333,stroke-width:2px".format(s_id))

    # Print Edges
    for c in connections:
        print("    {} <-->|Locked| {}".format(c[0], c[1]))

    if not connections:
        print("\n(No constraints found for selection)")