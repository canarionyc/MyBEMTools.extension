# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned

# pyrevit --version
# pyrevit caches clear --all

# pyrevit --usage > usage.txt
# pyrevit env > .\pyrevit_env.txt

# Configure pyRevit for current user from existing configuration file
#  pyrevit config -h 

# Manage pyRevit configurations
# pyrevit configs -h > configs_help.txt

# pyrevit attach master 342 2026 --allusers

# pyrevit configs routes -h > configs_routes_help.txt

# Enable the web server engine
# pyrevit configs routes enable # --log=configs_routes_enable.txt

# Enable the API that allows running scripts
# pyrevit configs routes coreapi enable

# (Optional) Set a specific port if 8080 is taken
# pyrevit configs routes port 8080

# C:\Users\admin\AppData\Roaming\pyRevit\2026
# C:\Users\admin\AppData\Roaming\Autodesk\Revit\Autodesk Revit 2026

# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned

param (
    [Parameter(Mandatory=$false)]
    [string]$ScriptPath = "C:\dev\MyBEMTools.extension\BEM.tab\Tools.panel\LiveTest.pushbutton\script.py",
    [Parameter(Mandatory=$false)]
    [string]$ModelPath = "C:\RevitAudit\model.rvt"
)

# 1. Check if the script file exists
if (-not (Test-Path -Path $ScriptPath)) {
    Write-Error "CRITICAL: The script file does not exist at: $ScriptPath"
    exit 1
}

# 2. Check if the file is zero size
$fileInfo = Get-Item -Path $ScriptPath
if ($fileInfo.Length -eq 0) {
    Write-Error "CRITICAL: The script file is empty (zero size): $ScriptPath"
    exit 1
}

Write-Host "Validation passed. Running script: $ScriptPath" -ForegroundColor Cyan

# pyrevit run "C:\dev\MyBEMTools.extension\BEM.tab\Tools.panel\LiveTest.pushbutton\script.py" --revit="C:\Program Files\Autodesk\Revit 2026\Revit.exe" `


# Execute pyRevit run with the parameters
pyrevit run "$ScriptPath" `
  "$ModelPath" `
  --revit="C:\Program Files\Autodesk\Revit 2026\Revit.exe" `
  --import="C:\dev\MyBEMTools.extension\lib"

