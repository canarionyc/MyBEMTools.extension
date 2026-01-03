# Revit 2025 Isolated Launcher
$RevitPath = "C:\Program Files\Autodesk\Revit 2025\Revit.exe"
$LanguageFlag = "/language ENU"

# 1. Clear PYTHONPATH for this session only
# This prevents other Python installs from interfering with pyRevit
$env:PYTHONPATH = $null
$env:PYTHONHOME = $null

# 2. Define a minimal System PATH
# We include only Windows defaults and the Revit directory
$MinimalPath = @(
    "C:\Windows\system32",
    "C:\Windows",
    "C:\Windows\System32\Wbem",
    "C:\Windows\System32\WindowsPowerShell\v1.0\",
    "C:\Program Files\Autodesk\Revit 2025\"
) -join ";"

$env:PATH = $MinimalPath

# 3. Inform the user
Write-Host "--- BEM Environment Isolation ---" -ForegroundColor Cyan
Write-Host "PYTHONPATH has been cleared for this session."
Write-Host "PATH has been restricted to essential directories."
Write-Host "Launching Revit 2025..."

# 4. Launch Revit
Start-Process -FilePath $RevitPath -ArgumentList $LanguageFlag