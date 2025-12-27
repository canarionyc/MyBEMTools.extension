#For most professional workflows, **stick with the `.exe` installer** you just used.
#
#Since you are managing both Revit 2025 (Legacy/Stable) and Revit 2026 (Modern/Beta), the installer provides the path of least resistance.
#
#---
#
#### Comparison: Installer vs. Git Clone
#
#| Feature | **Installer (.exe)** | **Git Clone (`gh repo clone`)** |
#| --- | --- | --- |
#| **Engines** | **Included.** (Installs IPY 2.7 and 3.4 automatically). | **Missing.** You must manually run `pyrevit install engine`. |
#| **Updates** | Download a new `.exe`. | Run `git pull` in the terminal. |
#| **Stability** | High (Tested releases). | Variable (Bleeding edge/Master branch). |
#| **Best For** | Daily production and BIM Managers. | Developers contributing to pyRevit itself. |
#
#---
#
#### Why the Installer is better for you right now:
#
#1. **The "Missing Engine" Trap:** As you saw earlier today, Git clones don't include the IronPython `.dll` files. This caused the "Object reference" errors and the inability to find engine `277`. The `.exe` handles all of this for you.
#2. **Environment Variables:** The installer correctly sets up your Windows Path, making the `pyrevit` command work reliably in PowerShell.
#3. **Stability in 2025:** Since you need Revit 2025 to be your "safe zone" for legacy code, the installer ensures the 2.7 engine is registered correctly without manual tinkering.
#
#### When should you use the Git Clone?
#
#You should only switch to the Git clone if:
#
#* You find a bug in Revit 2026 that was **just fixed** on GitHub this morning and hasn't been put into a new `.exe` yet.
#* You want to modify the pyRevit source code itself to add new features to the core platform.
#
#---
#
#### If you decide to switch to Git (The "Developer" Path)
#
#If you do decide to go the Git route later, you must remember to run these three commands immediately after cloning, otherwise your buttons won't work:
#
#```powershell
## 1. Register the new folder
#pyrevit clone master --path="C:\your\path\here"
#
## 2. Download the binary engines (The installer does this for you)
#pyrevit install engine 2712
#pyrevit install engine 342
#
## 3. Attach to Revit
#pyrevit attach master 2712 2025 --allusers
#
#```
#
#### My Advice
#
#**Stay with the `.exe` for now.** You have a working environment in Revit 2025 with the `2712` engine. Don't risk breaking the engine links while you are in the middle of recreating your model.
#
#**Would you like to proceed with the script to generate that 5m recessed window in your new, stable Revit 2025 environment?**

# 1. Register the new folder
pyrevit clone master --path="C:\your\path\here"

# 2. Download the binary engines (The installer does this for you)
pyrevit install engine 2712
pyrevit install engine 342

# 3. Attach to Revit
pyrevit attach master 2712 2025 --allusers