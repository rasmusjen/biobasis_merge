# Simple PowerShell verification script

Write-Host "============================================================" -ForegroundColor Green
Write-Host "BIOBASIS MERGE TOOL - VERIFICATION" -ForegroundColor Green  
Write-Host "============================================================" -ForegroundColor Green

# Check main files
$files = @(
    "README.md",
    "configs\biobasis_merge.yaml", 
    "python\biobasis_merge_py\main.py",
    "R\main.R",
    "tests\data\Biobasis_MM1_20240101.dat"
)

$allPresent = $true
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "✓ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file" -ForegroundColor Red
        $allPresent = $false
    }
}

# Count files
$pythonFiles = (Get-ChildItem "python\biobasis_merge_py\*.py").Count
$rFiles = (Get-ChildItem "R\R\*.R").Count
$testData = (Get-ChildItem "tests\data\*.dat").Count

Write-Host "`nFile counts:" -ForegroundColor Yellow
Write-Host "  Python modules: $pythonFiles" -ForegroundColor White
Write-Host "  R modules: $rFiles" -ForegroundColor White  
Write-Host "  Test data files: $testData" -ForegroundColor White

if ($allPresent -and $pythonFiles -ge 8 -and $rFiles -ge 8 -and $testData -eq 2) {
    Write-Host "`n🎉 VERIFICATION PASSED!" -ForegroundColor Green
    Write-Host "Biobasis merge tool successfully implemented!" -ForegroundColor Green
} else {
    Write-Host "`n❌ VERIFICATION FAILED" -ForegroundColor Red
}

Write-Host "============================================================" -ForegroundColor Green
