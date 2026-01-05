# --- BEM ENVIRONMENT INITIALIZATION v2 ---
$extPath = "C:\dev\MyBEMTools.extension"

# (Get-Item "C:\Program Files\Autodesk\Revit 2025\Revit.exe").VersionInfo.FileVersion

pyrevit extensions paths add C:\dev
pyrevit extensions paths 
pyrevit env --debug > pyrevit_env.txt

Write-Host "--- STEP 1: Extension Sanity Check ---" -ForegroundColor Cyan
if (Test-Path "$extPath\*.tab\*.panel\*.pushbutton\script.py") {
    Write-Host "[OK] pyRevit Bundle structure is valid." -ForegroundColor Green
} else {
    Write-Host "[FAIL] Extension structure is invalid. Ensure you have .tab, .panel, and .pushbutton folders." -ForegroundColor Red
}

Write-Host "--- STEP 2: Cleaning pyRevit Environment ---" -ForegroundColor Cyan
# Clear the attachment cache that might be holding the old 25.0.2.419 version info
Remove-Item "$env:APPDATA\pyRevit-Master" -Recurse -Force -ErrorAction SilentlyContinue

# Since your registry and hosts files are now correct, the issue might be a corrupted or blocked DLL in the engine folder. Because you are on Windows 10 Home, Windows "Zone.Identifier" flags can sometimes block the pyRevit loader from initializing correctly.

# Run these commands to "unblock" and refresh your installation:
# 1. Navigate to your pyRevit folder
cd C:\repos\pyRevit-Master

# 2. Unblock all files (Windows Home sometimes blocks downloaded DLLs)
Get-ChildItem -Path . -Recurse | Unblock-File

# get the enbines available for clone master
pyrevit clones engines master


# 3. Force pyRevit to forget the specific Revit attachment and start fresh
pyrevit detach 2025 
pyrevit attached
pyrevit attach master 342 2025 --allusers  
pyrevit attached

Write-Host "--- STEP 3: Environment Verification ---" -ForegroundColor Cyan
$envOut = pyrevit env
$envOut | Select-String "master", "2025", "Engine"

# Final check: Does the CLI now see the updated version?
if ($envOut -match "25.4.41.14") {
    Write-Host "[OK] pyRevit now recognizes Revit 2025.4.4" -ForegroundColor Green
} else {
    Write-Host "[WARNING] pyRevit still sees the old build. This may be a Registry issue." -ForegroundColor Yellow
}

Write-Host "Launching Revit 2025.4.4..." -ForegroundColor Yellow
& "C:\Program Files\Autodesk\Revit 2025\Revit.exe" /language ENU /nosplash

# look in 
# C:\Users\admin\AppData\Roaming\pyRevit

# %LOCALAPPDATA%\Autodesk\Revit\Autodesk Revit 2025\Journals