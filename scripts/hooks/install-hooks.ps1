#!/usr/bin/env pwsh
<#
Install git hooks for the repo. This script removes any existing pre-commit hooks
in both .git/hooks and the scripts/hooks directory (safe delete), then sets the
repository's hooks path to `scripts/hooks` so the versioned hooks are used.

Run this script from the repository root in PowerShell. It will remove any
existing pre-commit hook files and enable the new pre-commit hook we ship in
the `scripts/hooks` folder.
#>

$ErrorActionPreference = 'Stop'

Write-Host "Removing existing pre-commit hooks from '.git/hooks'..."
if (Test-Path -Path .git\hooks) {
    Get-ChildItem -Path .git\hooks -Filter "pre-commit*" -File -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "Removing: $($_.FullName)"
        Remove-Item -LiteralPath $_.FullName -Force
    }
}

Write-Host "Note: We do not delete versioned hook templates under 'scripts/hooks'. If you have old hook templates you can remove them manually."

Write-Host "Creating hooks folder if missing..."
New-Item -ItemType Directory -Force -Path scripts/hooks | Out-Null

Write-Host "Ensure your working tree includes versioned hook templates under 'scripts/hooks'."
Write-Host "If you want to use them, run: git config core.hooksPath scripts/hooks"

Write-Host "Setting git config core.hooksPath to 'scripts/hooks'"
git config core.hooksPath scripts/hooks

Write-Host "Installation completed. Run 'git commit' to test the pre-commit hook."
