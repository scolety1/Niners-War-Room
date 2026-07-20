# Validation results

| Gate | Result |
|---|---|
| Repository / ancestry | PASS: accepted HQ plus exact three commits plus one correction |
| Independent final reviews | PASS: two approvals |
| Focused launcher | PASS: 40 |
| Focused cross-domain bundle | PASS: 529 total |
| Hermetic | PASS: 2,688; exit 0 |
| LocalData | BLOCKED AS REQUIRED: exact marker; exit 4 |
| Security controls | PASS: 20/20; no new scan |
| PowerShell parser | PASS: four scripts |
| Python compile / changed Ruff | PASS |
| Live synthetic lifecycle | PASS: healthy/reuse/backup/restart/clean stop |
| Real migration | BLOCKED_INVALID_LEGACY_STATE; no mutation |
| One-click recovery | READY; real confirmation pending |
| Interactive install | READY package; real user pending |
| Primary CSV hashes | PASS: all five exact |
| Protected/frozen scope | PASS |

The only non-product failed attempts were harness/environment issues: sandbox denial of disposable Git metadata, long Windows path access, a missing intermediate Pytest directory, and a deliberately retained synthetic junction conflict. Each was rerun in the correct clean/owned environment without changing product semantics or waiving a test.
