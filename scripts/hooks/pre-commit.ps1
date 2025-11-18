#!/usr/bin/env pwsh
<# PowerShell pre-commit hook: run pytest, generate coverage badge, stage badge #>
$ErrorActionPreference = 'Stop'

Write-Host "Running tests..."
python -m pytest -q --maxfail=1

Write-Host "Generating coverage badge..."
try {
    python -m genbadge coverage -i coverage.xml -o coverage.svg
} catch {
    Write-Host "Failed to generate coverage badge: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Staging coverage.svg for commit..."
git add coverage.svg

Write-Host "Pre-commit hook: tests passed and coverage badge created." -ForegroundColor Green
