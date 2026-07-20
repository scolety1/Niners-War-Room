$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stableCheckout = 'C:\NWR\Niners-War-Room-V1'
$hqRef = 'refs/remotes/origin/work/hq-parallel-control'

if ([System.IO.Path]::GetFullPath($repoRoot).TrimEnd('\') -ine $stableCheckout.TrimEnd('\')) {
    throw "Run Data Health recovery from the stable canonical checkout only: $stableCheckout"
}
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.git') -PathType Container)) {
    throw 'The stable runtime must be a standalone clone with its own .git directory.'
}
$headCommit = (& git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot rev-parse HEAD).Trim()
$hqCommit = (& git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot rev-parse $hqRef).Trim()
if ($LASTEXITCODE -ne 0 -or -not $headCommit -or $headCommit -ne $hqCommit) {
    throw 'The stable runtime is not at the exact canonical HQ commit.'
}
$dirty = & git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot status --porcelain
if ($dirty) { throw 'Data Health recovery requires a clean canonical runtime checkout.' }

$current = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$sessionId = (Get-Process -Id $PID).SessionId
$explorers = @(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" | Where-Object {
    $_.SessionId -eq $sessionId
})
$owners = @($explorers | ForEach-Object {
    $owner = Invoke-CimMethod -InputObject $_ -MethodName GetOwner
    if ($owner.ReturnValue -eq 0) { "$($owner.Domain)\$($owner.User)" }
} | Select-Object -Unique)
if ($owners.Count -ne 1 -or $owners[0] -ne $current) {
    throw 'Interactive Explorer identity is unresolved or differs from the recovery identity.'
}
$localAppData = [Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)
if (-not $localAppData -or -not (Test-Path -LiteralPath $localAppData -PathType Container)) {
    throw 'The current user LocalAppData Known Folder could not be resolved.'
}

$pythonCandidates = @(
    (Join-Path $repoRoot '.venv\Scripts\python.exe'),
    'C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\python.exe'
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) { throw 'No supported Niners War Room Python runtime was found.' }

$receipt = 'C:\NWR\Niners-War-Room\local_exports\refresh_data\latest_refresh_status.json'
$recoveryRoot = Join-Path $localAppData 'NinersWarRoom\recovery\data-health'
Write-Host 'Niners War Room Data Health recovery resolved:'
Write-Host "  Windows user: $current"
Write-Host "  Corrupt receipt: $receipt"
Write-Host "  Recovery backup root: $recoveryRoot"
Write-Host "  Stable checkout: $repoRoot"
Write-Host "  Canonical commit: $headCommit"
Write-Host '  Action: preserve the canonical receipt-owned bytes, then quarantine only the corrupt latest receipt'
Write-Host '  No source refresh or successful receipt will be generated.'
$answer = Read-Host 'Type QUARANTINE_CORRUPT_RECEIPT to continue'
if ($answer -cne 'QUARANTINE_CORRUPT_RECEIPT') {
    throw 'Data Health recovery was not confirmed.'
}

& $python (Join-Path $PSScriptRoot 'nwr_desktop.py') recover-data-health --confirm $answer
if ($LASTEXITCODE -ne 0) { throw 'Niners War Room Data Health recovery did not complete.' }
Write-Host 'Recovery completed. Run Install Niners War Room Shortcut.ps1 next.'
