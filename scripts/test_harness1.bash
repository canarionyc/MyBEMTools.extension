#!/bin/bash
TARGET_DIR="/c/repos/pyRevit-Master/bin/netcore/engines/IPY342"

cat <<EOF > "$TARGET_DIR/pyRevitRunner.deps.json"
{
  "runtimeTarget": { "name": ".NETCoreApp,Version=v8.0" },
  "targets": {
    ".NETCoreApp,Version=v8.0": {
      "pyRevitRunner/1.0.0": {
        "runtime": { "pyRevitRunner.dll": {} },
        "dependencies": {
          "RevitAPI": "25.0.0.0",
          "RevitAPIUI": "25.0.0.0"
        }
      },
      "RevitAPI/25.0.0.0": { "runtime": { "RevitAPI.dll": { "assemblyVersion": "25.4.40.0", "fileVersion": "25.4.40.0" } } },
      "RevitAPIUI/25.0.0.0": { "runtime": { "RevitAPIUI.dll": { "assemblyVersion": "25.4.40.0", "fileVersion": "25.4.40.0" } } }
    }
  },
  "libraries": {
    "pyRevitRunner/1.0.0": { "type": "project", "serviceable": false, "sha512": "" },
    "RevitAPI/25.0.0.0": { "type": "reference", "serviceable": false, "sha512": "" },
    "RevitAPIUI/25.0.0.0": { "type": "reference", "serviceable": false, "sha512": "" }
  }
}
EOF
echo "Nuclear deps.json applied to $TARGET_DIR"
