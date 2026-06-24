# NWR RotoWire Source-Repair Candidate Report

Date: 2026-06-24

## Verdict

RotoWire is **blocked/manual**, not configured as a safe source-repair feed.

This lane did not scrape RotoWire, did not access a live RotoWire endpoint, did not copy raw quarantined files into the repository, and did not mutate approved unified universe artifacts.

## Starting Snapshot

- Branch: `codex/rotowire-scraper-source-repair-20260624`
- Base: `origin/work/hq-parallel-control` at `9924e6d60bd7e210f112a3887142fc37f47705e1`
- Consolidated unified universe rows: 368
- Missing player_id blockers: 5
- Missing age blockers: 16
- Age conflict rows: 1, Joshua Palmer
- `model_input_allowed=no` for all rows
- `app_wiring_allowed=no` for all rows

## RotoWire Availability

Current app/source policy treats RotoWire as manual/vendor-only:

- `src/services/data_refresh_orchestrator_service.py` registers `rotowire_vendor_exports` as `source_type=vendor_manual`, `safe_to_run=False`, `refresh_method=manual_export_only`, and `status=BLOCKED`.
- `docs/hq/draft_day_v2/NWR_REFRESH_DATA_BUTTON_AND_ORCHESTRATOR_V1_20260623.md` documents RotoWire/vendor exports as blocked/manual and not refreshed by the button.
- The Master quarantine audit preserved nine RotoWire-related research files outside the repo at `C:\NWR_LOCAL_ARCHIVE\rotowire_untracked_quarantine_20260624\`.
- The quarantined source contract says live pull is blocked pending terms/license review.

Quarantined files were inspected by filename/header/metadata and targeted policy lines only. They are not raw candidate player identity or age evidence. The available quarantined summary has `row_count=0`, `player_coverage_count=0`, `model_input_allowed=no`, `app_wiring_allowed=no`, and `source_truth_allowed=no`.

## Candidate Repair Results

Output table:

`docs/hq/model/unified_player_universe_v0/rotowire_candidate_id_age_repair_20260624.csv`

Counts:

- Candidate ID repairs: 0
- Candidate age repairs: 0
- Blocked rows: 19
- Review-needed rows: 1
- Do-not-use rows: 2
- Approved artifact mutations: 0

No candidate repair was produced because there is no licensed/configured safe RotoWire evidence row for the remaining blockers. RotoWire cannot be used as a tie-breaker for Joshua Palmer's approved-source age conflict, and DST age gaps should not be repaired with individual-player age data.

## Why Nothing Was Mutated

This was a candidate/source-repair lane only. The hard guardrails prohibit:

- wiring RotoWire into app pages,
- making RotoWire source truth,
- making RotoWire model truth,
- flipping `model_input_allowed` or `app_wiring_allowed` to `yes`,
- mutating approved unified universe artifacts,
- tracking raw vendor dumps or quarantined files.

The only repository outputs are a candidate table and this report.

## Master Integration Recommendation

Master should not integrate any player_id or age repairs from this lane because the candidate repair count is zero.

It is safe to integrate the report/table if the team wants a permanent record that RotoWire is currently blocked/manual for this source-repair use case. It is not necessary to rerun the readiness gate for data changes because no approved source-repair state changed.

If a future licensed/manual RotoWire export is approved and validated, then Master should integrate that source-repair evidence first and rerun or amend the unified universe readiness gate afterward.

## Readiness Gate Staleness

The readiness gate does not need to be upgraded from this lane. This lane produced no safe repairs and no approved artifact mutations.

If future RotoWire evidence is approved and changes missing ID/age blockers, the readiness gate should be rerun after those changes are integrated into Master.

## Guardrail Confirmation

- App pages changed: no.
- Model/rank/source-truth files changed: no.
- Approved unified artifacts changed: no.
- Frozen board changed: no.
- Latest/pinned files changed: no.
- Raw RotoWire/vendor files tracked: no.
- Quarantined files tracked: no.
- `C:\NWR_SHARED_DATA`, `local_exports`, and runtime JSON tracked: no.
