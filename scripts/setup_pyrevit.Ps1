# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned

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
pyrevit env 
pyrevit attached
pyret clones 
pyrevit  doctor 

# Remove the old clone registration
pyrevit clone forget master

# Register the new path
pyrevit clone master "C:\dev\pyRevit"


pyrevit run "C:\dev\MyBEMTools.extension\BEM.tab\Tools.panel\05_ModelTree.pushbutton\script.py" "C:\RevitAudit\model.rvt" --revit="C:\Program Files\Autodesk\Revit 2026\Revit.exe" --import="C:\dev\MyBEMTools.extension\lib"
