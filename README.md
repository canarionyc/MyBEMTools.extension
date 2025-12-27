# MyBEMTools.extension

Automated Building Energy Modeling (BEM) Auditing for Revit 2025+

## Overview

MyBEMTools is a specialized pyRevit extension designed to bridge the gap between complex BIM models and Energy Modeling workflows. It provides a robust framework for auditing model health and extracting geometric data, specifically optimized for the high-performance requirements of Revit 2025 and its transition to .NET 8.

## 🚀 Key Features

*   **Headless Auditing**: A CLI-ready pipeline for running batch audits via `pyrevit run`, enabling nightly model health checks without manual intervention.
*   **Live Listener (BIM Agent)**: A service-oriented architecture that allows external tools (bash, Python, web apps) to communicate with an open Revit instance via a local HTTP bridge.
*   **Revit 2025 Ready**: Fully compatible with the .NET 8 architecture, utilizing custom dependency configurations to maintain IronPython stability.
*   **Automated Data Scraper**: High-speed extraction of wall heights, volumes, and material thermal properties directly into JSON formats.

## 🛠 Architecture

This extension utilizes a dual-mode approach to handle the "fragility" of Revit API automation:

*   **Direct DB Interaction**: By strictly separating `Autodesk.Revit.DB` logic from the UI namespace, the tools can run in "headless" environments where no user interface exists.
*   **External Event Tunneling**: Uses an `IExternalEventHandler` bridge to safely execute background network commands on Revit’s single-threaded main loop.

## 📥 Installation

1.  Ensure [pyRevit](https://github.com/pyrevitlabs/pyRevit) is installed.
2.  Clone this repo into your pyRevit extensions folder:

    ```bash
    git clone https://github.com/canarionyc/MyBEMTools.extension.git
    ```

3.  Add the extension to pyRevit:

    ```bash
    pyrevit extend ui MyBEMTools "path/to/folder"
    ```

## Usage

### Headless Auditing

To run a headless audit, you can use a PowerShell script like the one below. This script executes a pyRevit command to run a specific script on a Revit model.

```powershell
# Add the extension's 'lib' directory to the Python path
$env:PYTHONPATH += ";C:\path\to\MyBEMTools.extension\lib"

# Define the script and model paths
$script = "C:\path\to\MyBEMTools.extension\BEM.tab\BuildCabana.panel\FromJSON.pushbutton\script.py"
$model  = "C:\path\to\your\model.rvt"

Write-Host "--- Starting Headless BEM Audit ---" -ForegroundColor Green

# Execute the audit using pyRevit CLI
pyrevit run $script $model --revit="C:\Program Files\Autodesk\Revit 2026\Revit.exe"

Write-Host "--- Audit Complete ---" -ForegroundColor Green
```

## File Structure

```
C:.
├───.idea
│   ├───fileTemplates
│   └───inspectionProfiles
├───BEM.tab
│   ├───BuildCabana.panel
│   │   └───FromJSON.pushbutton
│   ├───Lesson01.panel
│   │   └───Diagnostics.pulldown
│   │       ├───01_Environment.pushbutton
│   │       └───02_ModelHealth.pushbutton
│   ├───Lesson02.panel
│   │   ├───01_WallArea.pushbutton
│   │   ├───02_Tagging.pushbutton
│   │   ├───03_RoomVolume.pushbutton
│   │   └───04_MaterialAudit.pushbutton
│   ├───Lesson03.panel
│   │   └───Lessons.pulldown
│   │       ├───01_ThermalAudit.pushbutton
│   │       └───03_MaterialFix.pushbutton
│   └───Tools.panel
│       ├───05_ModelTree.pushbutton
│       ├───06_AlignLevels.pushbutton
│       ├───06_BEMAutomator.pushbutton
│       ├───07_RoofAutomator.pushbutton
│       ├───Diagnostics.pushbutton
│       ├───ExportCSV.pushbutton
│       ├───Listener.pushbutton
│       └───LiveTest.pushbutton
├───lib
│   └───__pycache__
└───scripts
```

🤖 ## Credits & Collaboration

This project is a product of a collaborative "Human-AI" engineering partnership.

*   **Lead Engineer**: [@canarionyc](https://github.com/canarionyc)
*   **Architectural Partner**: Gemini (Google AI) – Assisted in the deep-level debugging of the Revit 2025 .NET 8 migration, CLI "headless" bypass strategies, and the implementation of the asynchronous HTTP Listener architecture.
