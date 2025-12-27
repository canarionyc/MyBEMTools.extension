#!/bin/bash

# 1. Define Paths (Update these if your laptop paths differ)
TARGET_DIR="/c/repos/pyRevit-Master/bin/netcore/engines/IPY342"
PARENT_DIR="/c/repos/pyRevit-Master/bin/netcore"

echo "Step 1: Applying .NET 8 isolation to runtimeconfig.json..."

# This forces Revit to use .NET 8 and ignore the .NET 10 "Infection"
cat <<EOF > "$TARGET_DIR/pyRevitRunner.runtimeconfig.json"
{
  "runtimeOptions": {
    "tfm": "net8.0",
    "framework": {
      "name": "Microsoft.WindowsDesktop.App",
      "version": "8.0.0"
    },
    "rollForward": "Minor"
  }
}
EOF

echo "Step 2: Applying Version-Agnostic override to deps.json..."

# This bypasses the strict assembly version checks in Revit 2025.4.4
cat <<EOF > "$TARGET_DIR/pyRevitRunner.deps.json"
{
  "runtimeTarget": {
    "name": ".NETCoreApp,Version=v8.0",
    "signature": ""
  },
  "compilationOptions": {},
  "targets": {
    ".NETCoreApp,Version=v8.0": {
      "pyRevitRunner/1.0.0": {
        "runtime": {
          "pyRevitRunner.dll": {}
        }
      }
    }
  },
  "libraries": {
    "pyRevitRunner/1.0.0": {
      "type": "project",
      "serviceable": false,
      "sha512": ""
    }
  }
}
EOF

echo "Step 3: Syncing fixes to the parent directory..."
cp "$TARGET_DIR/pyRevitRunner.runtimeconfig.json" "$PARENT_DIR/pyRevitRunner.runtimeconfig.json"
cp "$TARGET_DIR/pyRevitRunner.deps.json" "$PARENT_DIR/pyRevitRunner.deps.json"

echo "Step 4: Setting session variables for .NET 8 stability..."
export DOTNET_ROLL_FORWARD="Minor"
export DOTNET_ROLL_FORWARD_ON_NO_CANDIDATE_FX=0

echo "------------------------------------------------------"
echo "SUCCESS: Environment fixed for Revit 2025.4.4"
echo "You can now run: pyrevit run ..."
