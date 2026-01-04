# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned

pyrevit --usage > usage.txt

# pyrevit --version
pyrevit caches clear --all
pyrevit doctor purge-installs

# pyrevit --usage > usage.txt

# Configure pyRevit for current user from existing configuration file
# pyrevit config -h 

# Manage pyRevit configurations
# pyrevit configs -h > configs_help.txt

# pyrevit attach master IPY342 2026 --allusers

# pyrevit configs routes -h > configs_routes_help.txt

# Enable the web server engine
# pyrevit configs routes enable # --log=configs_routes_enable.txt

# Enable the API that allows running scripts
# pyrevit configs routes coreapi enable

# (Optional) Set a specific port if 8080 is taken
# pyrevit configs routes port 8080

# Verifications
pyrevit -h
pyrevit env 

pyrevit clones 
pyrevit attached
pyrevit extensions
pyrevit releases
pyrevit revits
pyrevit caches
pyrevit.exe configs -h 
pyrevit.exe configs routes -h
pyrevit.exe configs routes coreapi enable


pyrevit-autocomplete.exe
pyrevit  doctor 

# Step 1 Remove the old clone registration
pyrevit clone forget master

# Register the new path
# pyrevit clone master "C:\repos\pyRevit-Master"

# If you already have the pyRevit files in C:\repos\pyRevit-Master, you don't need to "clone" them again from the internet. You just need to tell the pyRevit CLI that this folder exists and give it a name (like master).
pyrevit clones -h
pyrevit clones add master "C:\repos\pyRevit-Master"
pyrevit clones 
# ==> Registered Clones (full git repos)
# master | Deploy: "basepublic" | Branch: "develop" | Version: "5.3.1.25308+1659" | Path: "C:\repos\pyRevit-Master"
# ==> Registered Clones (deployed from archive/image)

# verfiy the engine
pyrevit clones engines master

# 2. Attach to Revit 2025
# Once the clone is registered, you must "attach" it so Revit 2025 knows to load it. Since Revit 2025 is a major shift to .NET 8, this step is critical.

pyrevit detach -h
pyrevit detach 2025


pyrevit attach -h

pyrevit attach master 2712 2025 --allusers
pyrevit attached

pyrevit extend ui MyBEMTools "C:\dev\MyBEMTools.extension"

pyrevit configs -h
pyrevit configs developer true
# Replace with your actual path to python.exe
pyrevit configs cpython "C:\Python312\python.exe"

pyrevit run "C:\dev\MyBEMTools.extension\BEM.tab\Tools.panel\05_ModelTree.pushbutton\script.py" "C:\RevitAudit\model.rvt" --revit="C:\Program Files\Autodesk\Revit 2026\Revit.exe" --import="C:\dev\MyBEMTools.extension\lib"

# routes
pyrevit configs -h
pyrevit configs checkupdates 
pyrevit configs routes 
pyrevit configs routes enable
# Ensure it uses your preferred port
pyrevit configs routes port 48884

pyrevit configs -h
pyrevit configs cpyversion 312

pyrevit config -h
#pyrevit config cpython engine "C:\Python312\python.exe"
pyrevit config --from="C:\Users\tglla\AppData\Roaming\pyRevit\pyRevit_config.ini" 
# This tells pyrevit exactly which python executable to use for engine 312

$myCode = "from pyrevit import routes; print(routes.get_routes())"; Invoke-RestMethod -Method Post -Uri "http://localhost:48884/BEM/exec" -Body $myCode

$myCode = "print('Hello from PowerShell')"; Invoke-RestMethod -Method Post -Uri "http://localhost:48884/BEM/exec" -Body $myCode

# This reads your script and 'pushes' it to the running Revit instance
Invoke-RestMethod -Method Post -Uri "http://localhost:48884/execute/" -Body (Get-Content "C:\dev\MyBEMTools.extension\scripts\test_thermal.py" -Raw)

# Syntax: pyrevit run <script_path> <revit_model_path_or_name>
pyrevit run "C:\dev\MyBEMTools.extension\scripts\test_thermal.py" "C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\Ejemplo1-2526_20251231.rvt"

.\Run-InRevit.ps1 .\test_connection.py

.\Run-InRevit.ps1 .\test_thermal.py

# extensions
pyrevit extensions -h
pyrevit extensions paths

# Revit logs in 
$ENV:LOCALAPPDATA
Set-Location "C:\Users\tglla\AppData\Local\Autodesk\Revit\Autodesk Revit 2026"

# i deleted c:/Users/tglla/AppData/Roaming/pyRevit/2025