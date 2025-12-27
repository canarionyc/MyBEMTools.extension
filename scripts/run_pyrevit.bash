# Clear potential .NET conflicts
#!/bin/bash

# 1. BARE ESSENTIALS PATH
export PATH="/c/Windows/system32:/c/Windows:/c/Program Files/dotnet:/c/Program Files/Git/cmd:/c/repos/pyRevit-Master/bin"
echo "PATH trimmed to: $PATH"

# 2. ISOLATION POLICY (Allow .NET 8 patches, block .NET 9/10)
unset DOTNET_ROOT
unset DOTNET_BUNDLE_EXTRACT_BASE_DIR
export DOTNET_ROLL_FORWARD="LatestPatch"
export DOTNET_ROLL_FORWARD_ON_NO_CANDIDATE_FX=0

echo "Roll Forward Policy: $DOTNET_ROLL_FORWARD"

#!/bin/bash
MODEL_PATH="C:\RevitAudit\Snowdon Towers Sample Structural.rvt"
SCRIPT_PATH="C:\dev\MyBEMTools.extension\BEM.tab\Tools.panel\Diagnostics.pushbutton\script.py"

# 1. Manually "Tunnel" the path through the OS environment
export MY_AUDIT_MODEL="$MODEL_PATH"

# 2. Run the command (providing the path twice ensures CLI validation passes)
pyrevit run "$SCRIPT_PATH" "$MODEL_PATH" --revit="2025"

# pyrevit run \
#   "C:\dev\MyBEMTools.extension\BEM.tab\Tools.panel\LiveTest.pushbutton\script.py" \
#   "C:\RevitAudit\Snowdon Towers Sample Structural.rvt" \
#   --revit="2025"


# pyrevit run "C:\Users\Public\script.py" "C:\RevitAudit\Snowdon Towers Sample Structural.rvt" --revit="2025"
