# C:\dev\RunAudit.ps1

$env:PYTHONPATH += ";C:\dev\MyBEMTools.extension\lib"
$env:DOTNET_ROLL_FORWARD = "LatestMajor"

# pyrevit attach master ipy342 2025

# add to "C:\repos\pyRevit-Master\bin\pyrevit-hosts.json"
#{
#        "build": "20251111_1515",
#        "meta": {
#            "schema": "1.0",
#            "source": "https://www.autodesk.com/support/technical/article/caas/tsarticles/ts/5t2muA1ysB6SddfImnbZDf.html"
#        },
#        "notes": "Revit 2025.4.4 Update",
#        "product": "Autodesk Revit",
#        "release": "2025.4.4",
#        "target": "x64",
#        "version": "25.4.41.14"
#    }

# 1. Setup Paths
# $OneDrivePath = "C:\Users\Usuario\OneDrive - Universidad de La Laguna\"
# C:\dev\MyBEMTools.extension\scripts\run_bem_audit_2025.ps1

# $script   = "C:\dev\MyBEMTools.extension\BEM.tab\BuildCabana.panel\FromJSON.pushbutton\script.py"
# $model    = "C:\RevitAudit\model.rvt"

$script ="C:\dev\MyBEMTools.extension\BEM.tab\Tools.panel\Diagnostics.pushbutton\script.py"
$model = "C:\RevitAudit\Snowdon Towers Sample Structural.rvt"

$template = "C:\RevitAudit\Custom_BEM_Template_2025.rte"
Set-ItemProperty "C:\RevitAudit\Custom_BEM_Template_2025.rte" -Name IsReadOnly -Value $false
# Standard Revit 2025 Default Template Path (adjust if your regional settings differ)
$default  = "C:\ProgramData\Autodesk\RVT 2025\Templates\Default_I_ENU.rte"

Write-Host "--- Starting Headless BEM Run (Revit 2025) ---" -ForegroundColor Green

# Logic: Find the best available 'Seed' file
if (Test-Path $model) {
    $target = $model
    Write-Host "Running on existing model." -ForegroundColor Cyan
}
elseif (Test-Path $template) {
    $target = $template
    Write-Host "Model missing. Starting from Custom Template." -ForegroundColor Yellow
}
elseif (Test-Path $default) {
    $target = $default
    Write-Host "Custom Template missing! Starting from Revit Default." -ForegroundColor Red
}
else {
    Write-Error "Critical Error: No seed files found at all. Check Revit installation."
    exit
}

# run as admin
# pyrevit attach master default 2025 --allusers

# Execute
# In your run_bem_audit_2025.ps1
$revitPath = "C:\Program Files\Autodesk\Revit 2025\Revit.exe"

# Use the full path in the --revit flag
# pyrevit run "$script" "$template" --revit="$revitPath" --debug

# Set the environment variable for this session only
$env:PYREVIT_RUNNER_REVIT = "2025"
$env:TARGET_MODEL_PATH = $model

# Now run the command without the path in the --revit flag
# The runner will see the variable above and look specifically for the 2025 attachment
pyrevit run "$script" "$model" --revit="2025"  --debug > "C:\RevitAudit\audit_log.txt"

#pyrevit run "$script" --revit="2025" --debug

Write-Host "--- Run Complete ---" -ForegroundColor Green

# 2. Sync from OneDrive to Local before starting
# Write-Host "Syncing latest model from OneDrive..."
# Copy-Item -Path $OneDrivePath -Destination $LocalWorkPath -Force