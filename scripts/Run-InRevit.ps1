param (
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Path,

    [Parameter(Mandatory=$false)]
    [int]$Port = 48884
)

# 1. Locate the file
$file = Get-Item -Path $Path -ErrorAction SilentlyContinue
if (-not $file) {
    Write-Host "Error: Could not find script at $Path" -ForegroundColor Red
    return
}

$scriptContent = Get-Content -Path $file.FullName -Raw
$uri = "http://localhost:$Port/BEM/exec"

Write-Host "Sending '$($file.Name)' to Revit..." -ForegroundColor Cyan

# 2. Send request WITHOUT throwing a terminal error on 500
# -SkipHttpErrorCheck is the key for PowerShell 7
$response = Invoke-WebRequest -Method Post -Uri $uri -Body $scriptContent -ContentType "text/plain" -SkipHttpErrorCheck

# 3. Handle the response based on status code
if ($response.StatusCode -eq 200) {
    Write-Host "--- Revit Output ---" -ForegroundColor Green
    $response.Content
    Write-Host "--------------------" -ForegroundColor Green
} 
else {
    Write-Host "--- Revit Logic Error ($($response.StatusCode)) ---" -ForegroundColor Red
    $response.Content
    Write-Host "----------------------------------" -ForegroundColor Red
}