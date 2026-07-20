param(
    [ValidateSet('start','stop','status','open-logs','backup','validate-data','restore-dry-run','restore','recover-data-health')]
    [string]$Command = 'status',
    [string]$SnapshotId = '',
    [string]$Confirm = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$pythonCandidates = @(
    (Join-Path $repoRoot '.venv\Scripts\python.exe'),
    'C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\python.exe'
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) {
    throw 'No supported NWR Python runtime was found.'
}
$arguments = @((Join-Path $PSScriptRoot 'nwr_desktop.py'), $Command)
if ($Command -in @('restore-dry-run','restore') -and -not $SnapshotId) {
    $SnapshotId = Read-Host 'Enter the exact Niners War Room backup snapshot ID'
}
if ($SnapshotId) { $arguments += $SnapshotId }
if ($Command -eq 'restore') { $arguments += @('--confirm', $Confirm) }
if ($Command -eq 'recover-data-health') {
    if (-not $Confirm) {
        $Confirm = Read-Host 'Type QUARANTINE_CORRUPT_RECEIPT to preserve and quarantine the corrupt receipt'
    }
    $arguments += @('--confirm', $Confirm)
}
& $python @arguments
exit $LASTEXITCODE
