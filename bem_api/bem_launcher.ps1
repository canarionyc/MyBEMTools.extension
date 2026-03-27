param (
    [Parameter(Mandatory=$false, Position=0)]
    [ValidateSet("levels", "walls", "all")]
    [string]$Target
)

# --- CONFIGURATION ---
$PythonExe = "C:\Python312\python.exe"
$Transmitter = "C:\dev\MyBEMTools.extension\bem_api\transmit_to_revit.py"
$PayloadDir = "C:\dev\MyBEMTools.extension\bem_api\payloads"

# --- VALIDATION ---
if (-not $Target) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " BEM API LAUNCHER" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Please specify which payload to send." -ForegroundColor Yellow
    Write-Host "Usage: .\bem_launcher.ps1 [levels | walls]" -ForegroundColor Gray
    Write-Host "Example: .\bem_launcher.ps1 levels" -ForegroundColor Gray
    exit
}

# --- ROUTING ---
if ($Target -eq "levels") {
    $Payload = "$PayloadDir\level_maker.json"
} 
elseif ($Target -eq "walls") {
    $Payload = "$PayloadDir\wall_maker.json"
}

# --- EXECUTION ---
Write-Host "Sending '$Target' payload to Revit..." -ForegroundColor Green
Write-Host "Executing: & $PythonExe $Transmitter $Payload" -ForegroundColor DarkGray

# The '&' symbol in PowerShell tells it to execute the string as a command
& $PythonExe $Transmitter $Payload

Write-Host "Done." -ForegroundColor Green