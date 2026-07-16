[CmdletBinding()]
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$repo = [IO.Path]::GetFullPath($RepoRoot)
$gate = Join-Path $repo "scripts\verify-repository.ps1"
if (-not (Test-Path -LiteralPath $gate -PathType Leaf)) {
    throw "Hermetic repository verification gate is missing: $gate"
}

& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
    -File $gate -Tier Hermetic -RepoRoot $repo
$code = $LASTEXITCODE
if ($code -ne 0) { exit $code }

Write-Host "Niners War Room static check passed through the Hermetic tier."
