# 1. Define the search path and keywords
$journalPath = "$env:LOCALAPPDATA\Autodesk\Revit\Autodesk Revit 2025\Journals"
$keywords = @("error", "exception", "failed", "pyrevit", "conflict", "assembly", "remoting")

# 2. Get the 3 most recently modified journal files
$latestJournals = Get-ChildItem -Path $journalPath -Filter "journal.*.txt" | 
                  Sort-Object LastWriteTime -Descending | 
                  Select-Object -First 3

Write-Host "--- Searching latest journals for BEM/pyRevit issues ---" -ForegroundColor Cyan

# 3. Perform the 'grep' (Select-String)
foreach ($file in $latestJournals) {
    Write-Host "`nScanning: $($file.Name) (Modified: $($file.LastWriteTime))" -ForegroundColor Yellow
    
    # Select-String is the PowerShell equivalent of grep
    # -Context 2,2 shows 2 lines before and 2 lines after the match
    $matches = Select-String -Path $file.FullName -Pattern $keywords -Context 2,2
    
    if ($matches) {
        $matches | ForEach-Object {
            Write-Host "Match found on line $($_.LineNumber):" -ForegroundColor White
            $_.Context.PreContext | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            Write-Host "> $($_.Line.Trim())" -ForegroundColor Red
            $_.Context.PostContext | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            Write-Host ("-" * 40) -ForegroundColor DarkGray
        }
    } else {
        Write-Host "No critical errors found in this file." -ForegroundColor Green
    }
}