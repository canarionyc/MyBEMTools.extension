cd "C:\repos\pyRevit-Master"

# 1. Initialize git in this folder
git init

# 2. Add the official pyRevit remote
git remote add origin https://github.com/eirannejad/pyRevit.git

# 3. Fetch the latest data from the server
git fetch

# 4. Force your folder to match the 'develop' branch 
# (This is the branch with the Revit 2025 .NET 8 fixes)
git reset --hard origin/develop

PS C:\repos\pyRevit-Master> pyrevit caches clear --all
PS C:\repos\pyRevit-Master>
PS C:\repos\pyRevit-Master> # 2. Re-link to Revit 2025 (using the engine you have)
PS C:\repos\pyRevit-Master> pyrevit attach master ipy342 2025
PS C:\repos\pyRevit-Master> pyrevit caches clear --all

git config --global --add safe.directory C:/repos/pyRevit-Master