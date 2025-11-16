#!/usr/bin/env pwsh
<#
Git pre-commit hook for PowerShell:
 - run pytest (with coverage.xml generated)
 - run genbadge to update coverage.svg when available
#>

Write-Host "[pre-commit] Running pytest (generates coverage.xml)"
& python -m pytest -q --maxfail=1 --disable-warnings --cov=. --cov-report=xml:coverage.xml
if ($LASTEXITCODE -ne 0) {
    Write-Error "[pre-commit] pytest failed - aborting commit"
    exit $LASTEXITCODE
}

Write-Host "[pre-commit] pytest succeeded"

if (Get-Command -Name genbadge -ErrorAction SilentlyContinue) {
    Write-Host "[pre-commit] Generating coverage badge (coverage.svg)"
    genbadge coverage -i coverage.xml -o coverage.svg
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[pre-commit] genbadge failed - aborting commit"
        exit $LASTEXITCODE
    }
    Write-Host "[pre-commit] coverage.svg updated"
} else {
    Write-Warning "[pre-commit] genbadge not found - skipping badge generation"
    Write-Host "Install with: python -m pip install genbadge"
}

exit 0