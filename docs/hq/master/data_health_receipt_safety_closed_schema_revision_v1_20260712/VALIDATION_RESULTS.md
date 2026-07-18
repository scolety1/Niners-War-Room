# Validation Results

Validation date: 2026-07-13 America/Denver. Commands used the bundled Python 3.12.13 runtime
and a short writable basetemp.

## Repository gates

- `git fetch --all --prune`: pass.
- Live `origin/work/hq-parallel-control`: `6bcb9c3c36fc560c30151591feaeff9d3960499f`.
- Expected/live difference: none.
- Source parent equals live HQ: pass.
- Successor base equals `e94960fa81195e92b332db6beef3229056c7d968`: pass.
- Blocked review commit/packet inspected read-only: pass.

## Automated results

| Gate | Result |
|---|---|
| Focused receipt/truth/panel/route plus new safety/page matrix | `68 passed in 11.44s` final rerun |
| Exact inherited regression command | `87 passed in 29.66s` |
| Route smoke alone | `2 passed in 2.26s` |
| Page-open state matrix | `14 passed in 7.80s` |
| Refresh orchestrator service | `19 passed in 23.03s` |
| Freshness/Recovery/Trust/source-governance/navigation protected set | `36 passed in 1.52s` |
| Ruff changed Python paths | pass |
| Python compilation changed Python paths | pass |
| `git diff --check` | pass |
| Protected Refresh Recovery and Decision Trust diff | zero |

## Differential result

Valid refresh state presentation, latest-success/LKG relationships, eight recovery states,
orchestrator execution, and freshness tests are unchanged and green. The revision delta is
limited to v2 receipt projection/validation/transaction behavior and passive inspection.
Behavior intentionally changed only for previously accepted unsafe/invalid receipt content
and display-triggered quarantine.

## Storage and privacy

- Successful final bytes are at or below 2 MiB: pass.
- Every rejected-write tree snapshot is identical: pass.
- Interrupted latest replace rollback is identical and leaves no temp: pass.
- Duplicate key, invalid type, unsupported schema, corrupt latest/backup read-only checks:
  pass.
- Secret/header/token/cookie/provider/path rejection: pass.
- Tracked receipt storage files: zero.
- Storage boundary: ignored local `local_exports/refresh_data` only.

## Packet

- Required top-level files: 20.
- CSV files: 4; constant column counts and non-empty bodies required.
- `MANIFEST.json`: strict duplicate-key parse required.
- Historical source/review packets: unchanged.
