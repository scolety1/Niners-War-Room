# RotoWire Overnight Completeness Audit

Date: 2026-05-17

Status: completed checklist, review-only

## Result

The overnight run satisfied the requested safe-build scope. No active app
rankings, My Team output, War Board output, or readiness gates were changed.

Post-check correction: a code review found that confidence was contributing
positive private value and that missing components were displayed as numeric
zeroes. Both were patched. Confidence is now receipt/cap-only, and missing
component evidence now has blank score/contribution values.

Pre-audit correction: first-down-aware replacement/VORP is now implemented in a
review-only form. The current RotoWire exports do not include direct
rushing/receiving first-down fields, so 2025 first downs are estimated from
source-safe 2022-2024 nflverse first-down history and labeled
`estimated_from_history`.

## Task Checklist

| Requested task | Status | Evidence |
| --- | --- | --- |
| Finish validating RotoWire replacement baseline | done | `local_exports/model_v4/rotowire_replacement/latest/` plus tests. |
| Finish validating VORP review layer | done | `local_exports/model_v4/rotowire_vorp_review/latest/` plus tests. |
| Patch runtime/test bugs | done | Fixed Ruff long-line issue in VORP service; all tests pass. |
| Generate review-only VORP outputs | done | 80 VORP rows, 37 positive VORP players after first-down estimate layer. |
| Create first-down-aware replacement/VORP plan | done | `docs/model_v4/ROTOWIRE_FIRST_DOWN_AWARE_REPLACEMENT_PLAN.md`. |
| Use direct first-down fields only if present | done | RotoWire direct first-down fields not found; nflverse direct first-down history powers estimates. |
| Label estimates as estimated_from_history | done | Replacement and VORP summaries expose `estimated_from_history`. |
| Never treat estimated first downs as direct data | done | Receipts and warnings label estimates as non-direct. |
| Build review-only dynasty candidate layer | done | `local_exports/model_v4/rotowire_dynasty_candidate/latest/`. |
| Use stats-first evidence | done | Candidate layer uses stats-first output. |
| Use replacement/VORP logic | done | Candidate layer joins VORP review rows. |
| Use Deep Research position weights | done | Position-specific candidate weights added. |
| Add age/dropoff | done | Age caps and age receipts added. |
| Use snap/route/target evidence where licensed | done | Candidate layer uses RotoWire role/route target receipts. |
| Apply confidence caps for missing evidence | done | Incoming no-evidence players remain weak/review. |
| Keep projections out of private football value | done | Summary shows projection rows used for core value = 0. |
| Keep ADP/rankings/market/league rank out | done | Summary shows market and league-rank use = false. |
| Add/update receipts | done | 480 receipt rows. |
| Run sanity fixtures | done | Candidate sanity review generated: 12 ready, 1 review, 0 blocked. |
| Run named-player review | done | Candidate named-player review generated. |
| Produce checkpoint docs | done | Golden checkpoint, first-down plan, next patch list, roadmap update. |
| Run focused tests | done | Focused replacement/VORP/candidate tests pass. |
| Run Ruff on touched files | done | Passed. |
| Run full static check if practical | done | `pytest` 907 passed; `ruff check .` passed. |
| Prepare external audit packet | done | Audit zip generated without raw licensed RotoWire exports. |

## Verification Commands

```text
python -m pytest tests/test_model_v4_rotowire_replacement_baseline_service.py tests/test_model_v4_rotowire_vorp_review_service.py tests/test_model_v4_rotowire_dynasty_candidate_service.py
python -m pytest
python -m ruff check .
```

Observed result:

```text
focused tests: 18 passed
full tests: 907 passed
ruff: all checks passed
```

Ruff emitted access-denied warnings for temporary folders but returned success
and reported no lint failures.

## Packet Safety Check

Audit packet:

`local_exports/model_v4/audit_packets/rotowire_golden_candidate_external_audit_20260517_043643.zip`

The packet includes derived docs, review outputs, selected implementation
files, and selected tests only. It does not include:

- `raw_user_exports`
- raw RotoWire downloads
- local Downloads files
- raw intake clean rows from the full licensed export set

## Known Remaining Work

1. Integrate incoming rookie/prospect data once available.
2. Audit Malik Nabers, Brian Thomas Jr., and Luther Burden receipts before any
   formula patch.
3. Audit first-down estimation effects before app promotion.
4. Add injury severity mapping; keep unsourced health out of value.
5. Run external audit against the first-down-aware review-only packet.

## Do Not Promote Yet

The model is not roster-decision-ready, draft-ready, or final-money-ready.

Next safest action: run external audit before asking the app to use the
candidate layer for real decisions.
