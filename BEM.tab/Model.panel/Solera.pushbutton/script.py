#! python3
# -*- coding: utf-8 -*-

# %% IMPORTS AND SETUP
import json
import os
import clr
from typing import List as PyList, Dict, Any

# 1. Bypass pyRevit entirely; use raw Autodesk API
clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB

# 2. Import .NET Core System components for Python.NET strict typing
import System
from System.Collections.Generic import List as DotNetList

# %% CONFIGURATION
# Set the absolute path to your cadastral JSON file
JSON_PATH: str = r"C:\dev\PteZurita\output\parcel_polylines.json"

# Cadastral UTM coordinates are in meters (1 meter = 1 / 0.3048 feet)
M_TO_FT: float = 1.0 / 0.3048


# %% MAIN GENERATOR LOGIC
def generate_soleras_from_json() -> None:
    doc: DB.Document = __revit__.ActiveUIDocument.Document

    # %% FILE PARSING
    if not os.path.exists(JSON_PATH):
        print(f"❌ ERROR: JSON file not found at {JSON_PATH}")
        return

    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data: Dict[str, Any] = json.load(f)
    except Exception as e:
        print(f"❌ ERROR: Failed to read JSON. {e}")
        return

    polylines_data: PyList[Dict[str, Any]] = data.get("polylines", [])

    if not polylines_data:
        print("⚠️ No polylines found in the selected JSON.")
        return

    # %% RELEVANT REVIT ELEMENTS
    floor_type_id: DB.ElementId = doc.GetDefaultElementTypeId(DB.ElementTypeGroup.FloorType)
    level: DB.Level = doc.ActiveView.GenLevel

    if not level:
        print("❌ ERROR: Please run this script from a Plan View with an associated Level.")
        return

    print(f"🚀 Starting Solera Generation. Target Level: {level.Name}")
    print("-" * 50)

    # %% TRANSACTION TO CREATE FLOORS
    created_floors_count: int = 0
    t: DB.Transaction = DB.Transaction(doc, "Generate Multiple Soleras")
    t.Start()

    try:
        for idx, poly_dict in enumerate(polylines_data):
            print(f"Processing Polyline {idx + 1}/{len(polylines_data)}...")
            increments: PyList[Dict[str, float]] = poly_dict.get("relative_increments", [])

            if len(increments) < 3:
                print(f"  -> Skipped: Only {len(increments)} vertices. A floor needs at least 3.")
                continue

            points: PyList[DB.XYZ] = []
            for inc in increments:
                x_m: float = inc.get("dx", 0.0)
                y_m: float = inc.get("dy", 0.0)
                points.append(DB.XYZ(x_m * M_TO_FT, y_m * M_TO_FT, 0.0))

            is_closed: bool = points[0].IsAlmostEqualTo(points[-1])
            num_points: int = len(points) if not is_closed else len(points) - 1
            print(f"  -> Extracted {num_points} distinct vertices.")

            curve_loop: DB.CurveLoop = DB.CurveLoop()

            for i in range(num_points):
                p1: DB.XYZ = points[i]
                p2: DB.XYZ = points[(i + 1) % num_points]

                if not p1.IsAlmostEqualTo(p2):
                    line: DB.Line = DB.Line.CreateBound(p1, p2)
                    curve_loop.Append(line)

            # --- THE CRITICAL .NET FIX ---
            # Instantiate a strongly typed .NET List and add the curve_loop
            dot_net_loop_list = DotNetList[DB.CurveLoop]()
            dot_net_loop_list.Add(curve_loop)

            print("  -> Creating Floor element in database...")

            # Pass the strictly typed .NET List instead of the Python List
            new_floor = DB.Floor.Create(doc, dot_net_loop_list, floor_type_id, level.Id)

            if new_floor:
                print(f"  -> ✅ Success! Floor ID: {new_floor.Id}")
                created_floors_count += 1
            print("-" * 50)

        t.Commit()
        print(f"🎉 Job Complete: Successfully generated {created_floors_count} solera(s).")

    except Exception as e:
        t.RollBack()
        print(f"❌ Transaction failed and rolled back during Polyline {idx + 1}: {e}")


if __name__ == "__main__":
    generate_soleras_from_json()