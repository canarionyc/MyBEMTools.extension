# C:\dev\RunAudit.ps1

$env:PYTHONPATH += ";C:\dev\MyBEMTools.extension\lib"

# 1. Setup Paths
# $OneDrivePath = "C:\Users\Usuario\OneDrive - Universidad de La Laguna\"
# $script = "C:\dev\MyBEMTools.extension\BEM.tab\Tools.panel\05_ModelTree.pushbutton\script.py"
$script = "C:\dev\MyBEMTools.extension\BEM.tab\BuildCabana.panel\FromJSON.pushbutton\script.py"
# $model  = "C:\Users\Usuario\OneDrive - Universidad de La Laguna\Revit\Ejemplo1-2526-main\EJEMPLO1-2526_20251222.rvt" # Ensure this path is correct
$model  = "C:\RevitAudit\model.rvt"
# $model  =   "H:\My Drive\Revit_ws\model.rvt"

Write-Host "--- Starting Headless BEM Audit (Revit 2026) ---" -ForegroundColor Green

# 2. Execute via CLI
# --purge: Cleans up temporary journal files
# --revit=2026: Forces the specific version
pyrevit run $script $model --revit="C:\Program Files\Autodesk\Revit 2026\Revit.exe" # --purge --debug

Write-Host "--- Audit Complete ---" -ForegroundColor Green

# 2. Sync from OneDrive to Local before starting
# Write-Host "Syncing latest model from OneDrive..."
# Copy-Item -Path $OneDrivePath -Destination $LocalWorkPath -Force