@echo off
:: Starts a local environment scope. 
:: Any changes made after this line are discarded when the script ends or at endlocal.
setlocal

echo --- BEM Environment Isolation (BAT) ---

:: 1. Clear Python variables to prevent pyRevit/pythonnet conflicts
set PYTHONPATH=
set PYTHONHOME=

:: 2. Set a minimal PATH (Windows defaults + Revit 2025)
set PATH=C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Program Files\Autodesk\Revit 2025

echo PYTHONPATH has been cleared.
echo PATH has been restricted.
echo Launching Revit 2025 ENU...

:: 3. Start Revit
:: The "" is for the window title (required by the 'start' command when paths have quotes)
start "" "C:\Program Files\Autodesk\Revit 2025\Revit.exe" /language ENU

echo Revit process started. Cleaning up environment...

:: 4. Revert environment variables to their original state
endlocal

echo --- Done ---