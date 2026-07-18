# Validation Results

All commands ran from the isolated worktree on 2026-07-13 using the bundled Python 3.12.13 runtime where shown.

## Repository and design gate

- `git fetch --all --prune` completed.
- `git rev-parse refs/remotes/origin/work/hq-parallel-control` returned `6bcb9c3c36fc560c30151591feaeff9d3960499f`, exactly matching the required HQ baseline. Remote advance count: 0.
- The isolated branch is `work/data-health-guardrail-truth-receipt-durability-v1-20260712`.
- `RECEIPT_STORAGE_AND_SCHEMA_DECISION.md` and `FIELD_AND_LIFECYCLE_REUSE_MAP.csv` were created before service/application implementation. Decision: `DESIGN_GATE_APPROVED_FOR_BOUNDED_IMPLEMENTATION`.

## Focused and regression tests

Command:

```text
python -m pytest tests/test_refresh_receipt_store_service.py tests/test_data_health_receipt_truth.py tests/test_durable_refresh_receipt_panel_render.py tests/test_data_health_receipt_route_smoke.py tests/test_data_health_dashboard_service.py tests/test_data_refresh_orchestrator_service.py tests/test_refresh_recovery_presentation_service.py tests/test_refresh_recovery_panel_render.py tests/test_source_governance_service.py tests/test_navigation_compression.py tests/test_decision_trust_strip_service.py tests/test_decision_trust_strip_render.py tests/test_decision_trust_strip_surfaces.py --basetemp=C:\Users\codex-agent\Documents\Niners War Room\dh-test-tmp\regression-final-20260713
```

Result: `87 passed in 29.30s`.

Breakdown: receipt store 9; receipt truth 9; durable panel 2; affected-route no-side-effect smoke 2; Data Health dashboard 13; orchestrator 19; canonical Refresh Recovery 5; source-governance presentation 1; navigation 17; Decision Trust Strip 10. New focused receipt/truth/panel/route coverage totals 22 passing tests.

The focused cases cover current success, stale success, partial success, failed with/without last-known-good, skipped, unavailable, gated, missing, corrupt, unsupported, duplicate-key, truncated, oversized, corrupt latest plus corrupt backup, validated backup, identity exception, source exception, not enough information, atomic replace, retention, forbidden metadata, rerun, fresh-app load, and no page-open mutation.

## Static validation

- `python -m ruff check` over every changed Python/test file: `All checks passed!`.
- `python -m compileall -q` over every changed Python/test file: exit 0.
- `git diff --check`: exit 0.
- `git diff --cached --check`: required immediately before the single local commit; exit 0.

## Packet validation

- Python `csv.reader` parsed all four packet CSV files and 77 data rows, requiring non-empty headers, non-empty bodies, and a constant column count per file.
- Python strict JSON parsing used the receipt duplicate-key hook on `MANIFEST.json`; no duplicate keys and schema shape/version 1 passed.
- Manifest required-file set equals the 18 required top-level packet files.
- All three rendered-evidence files exist and their byte counts/SHA-256 digests match `MANIFEST.json`.
- No required packet file is empty.

## Storage, privacy, and protected paths

- `git ls-files -- local_exports/refresh_data` returned no tracked files.
- `git status --short --ignored -- local_exports/refresh_data` reported the local root as ignored.
- High-risk credential signature scan found no access keys, GitHub tokens, OpenAI-style secret keys, or private-key blocks in changed files.
- Source-governance service diff exit: 0 (unchanged).
- Freshness-threshold addition scan over application/service additions: none.
- Implementation path scan found no Player Compare, Trading Lab, ranking, formula, recommendation, source-governance, plugin, rookie, roster-hydration, draft, frozen, or 2026 artifact path.
- Orchestrator zero-context diff contains only the receipt-store import plus `write_refresh_status`/`load_latest_refresh_status` delegation; selection, order, registry, retry, timeout, and execution code are unchanged.

Protected blob equality against starting HEAD:

| Path | Git blob | Match |
|---|---|---|
| `src/services/refresh_recovery_presentation_service.py` | `b295662ce49396478e57375890aa82d0395bae27` | true |
| `app/components/refresh_recovery_panel.py` | `002f7e6bbc1e7ffb56210fa266576ab1e7c93ae4` | true |
| `src/services/decision_trust_strip_service.py` | `8672811336a9614f3e3c9dcdedfdf1c642f3a9ef` | true |
| `app/components/decision_trust_strip.py` | `7319308a4342396a6dcf26514b86697310adec96` | true |

## Rendered evidence

Controlled browser review inspected the Refresh Data and Settings / Data Health routes without invoking a refresh. The retained evidence set contains one desktop state matrix, one 375 by 812 expanded compact view, and one desktop Data Health guardrail view. The matrix visibly includes all eight canonical recovery states across clearly labeled synthetic sources. Missing, unsupported, and corrupt messages were also inspected during controlled reloads; their mechanical coverage remains in the tests.

Rendered evidence files: 3. Synthetic fixture labels: present. Production/provider data: absent.
