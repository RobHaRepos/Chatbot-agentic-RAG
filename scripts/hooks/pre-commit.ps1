#!/usr/bin/env pwsh
<#
PowerShell-only Git pre-commit hook (moved to a .ps1 file so the top-level 'pre-commit'
script can be a cross-platform shell wrapper). This runs pytest with coverage and optionally
generates a coverage badge.
#>

param([string[]] $args)

Write-Host "[pre-commit.ps1] Running pytest (generates coverage.xml)"

# Prefers repo venv python
$projectVenvWin = Join-Path -Path $PSScriptRoot -ChildPath "..\.venv\Scripts\python.exe" | Resolve-Path -ErrorAction SilentlyContinue
$projectVenvPosix = Join-Path -Path $PSScriptRoot -ChildPath "../.venv/bin/python" | Resolve-Path -ErrorAction SilentlyContinue

if ($projectVenvWin) {
    $PYTHON = $projectVenvWin -replace "\\`n",""
} elseif ($projectVenvPosix) {
    $PYTHON = $projectVenvPosix -replace "\\`n",""
} elseif (Get-Command -Name python -ErrorAction SilentlyContinue) {
    $PYTHON = (Get-Command -Name python).Source
} elseif (Get-Command -Name py -ErrorAction SilentlyContinue) {
    $PYTHON = (Get-Command -Name py).Source
} else {
    $PYTHON = "python"
}

Write-Host "[pre-commit.ps1] Using python: $PYTHON"
try {
    & $PYTHON -m pytest -q --maxfail=1 --disable-warnings --cov=. --cov-report=xml:coverage.xml
} catch {
    if ($_.Exception.Message -match "No module named pytest") {
        $msg = @"
[pre-commit.ps1] pytest is not installed in $PYTHON.
Install with:
    $PYTHON -m pip install -r requirements-ci.txt

Or create a local .venv and install deps:
    python -m venv .venv; . .venv/Scripts/Activate.ps1; pip install -r requirements-ci.txt
"@
        Write-Error $msg
    } else {
        Write-Error "[pre-commit.ps1] pytest failed: $_"
    }
    exit 1
}

if (Get-Command -Name genbadge -ErrorAction SilentlyContinue) {
    Write-Host "[pre-commit.ps1] Generating coverage badge (coverage.svg)"
    genbadge coverage -i coverage.xml -o coverage.svg
    if ($LASTEXITCODE -ne 0) { Write-Error "[pre-commit.ps1] genbadge failed - aborting commit"; exit $LASTEXITCODE }
    # Stage coverage badge
    if (Get-Command -Name git -ErrorAction SilentlyContinue) {
        Write-Host "[pre-commit.ps1] Staging coverage.svg for commit"
        git add coverage.svg
    }
} else {
    Write-Warning "[pre-commit.ps1] genbadge not found - skipping badge generation"
}

exit 0
