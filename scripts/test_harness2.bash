#!/bin/bash
DEBUG_FILE="C:/Users/Public/pyrevit_headless_debug.txt"

echo "--- HEADLESS ENGINE CHECK ---"
if [ -f "$DEBUG_FILE" ]; then
    cat "$DEBUG_FILE"
    # rm "$DEBUG_FILE"
else
    echo "CRITICAL: The script failed to generate the debug file."
    echo "Check the Revit Journal for 'TaskScriptEngine' exceptions."
fi
