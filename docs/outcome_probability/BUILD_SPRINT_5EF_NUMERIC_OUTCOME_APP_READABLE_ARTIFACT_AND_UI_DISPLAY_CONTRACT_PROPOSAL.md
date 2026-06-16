# Sprint 5EF - Numeric Outcome App-Readable Artifact And UI Display Contract Proposal

## Purpose

Sprint 5EF proposes a future app-readable artifact and UI display contract for numeric Outcome probabilities. This sprint is design only. It does not create the app-readable artifact, edit UI/source files, wire app display, create rankings/sorting behavior, create hidden sort keys, create promoted artifacts, push, deploy, or release.

## Approved Display Heads From 5EA-5EE

Approved for a future app-readable/display proposal:

| Head | UI label proposal | Status |
| --- | --- | --- |
| `qb_t12` | QB Top 12 | Approved for future numeric display proposal |
| `rb_t12` | RB Top 12 | Approved for future numeric display proposal |
| `rb_t24` | RB Top 24 | Approved for future numeric display proposal after 5EC GREEN dry-run upgrade; carry caution note |
| `wr_t12` | WR Top 12 | Approved for future numeric display proposal |
| `wr_t24` | WR Top 24 | Approved for future numeric display proposal |
| `wr_t36` | WR Top 36 | Approved for future numeric display proposal |
| `te_t12` | TE Top 12 | Approved for future numeric display proposal |

No other heads may be included in the first numeric app-readable artifact proposal.

## Display Policy

Future UI display should show integer percentages only:

- no decimals;
- no hidden higher-precision app fields;
- no high-precision app-readable columns that are rounded only at render time;
- no sortable numeric probability backing fields;
- no coarse display bands in the first numeric artifact proposal.

Local-only audit exports may retain probability audit units for review, but app-readable artifacts must carry display-safe integer percentage fields only if a later implementation sprint explicitly approves them.

## Tooltip And Copy Rules

Tooltips should describe the numbers as private model estimates from admitted prior-season evidence, not certainties.

Required copy principles:

- avoid fake precision;
- name the threshold plainly;
- state that missing evidence shows unavailable;
- state that market, rankings, ADP, projections, consensus, startup, and trade-calculator sources are not used;
- state that probabilities do not affect ranking or sorting.

Example tooltip pattern:

`Private Outcome estimate for finishing as a {position} Top {threshold}. Uses admitted source-safe football evidence only. Unavailable means required evidence is missing or the player is unsupported. Not used for sorting.`

## Null And Unavailable Behavior

Rows that are unsupported, missing required features, rookie-ineligible for veteran heads, kicker rows, or blocked by join/provenance checks must display `unavailable` or an em dash, not `0%`.

Unavailable reason fields may be useful for QA, but they must not become hidden sort keys or ranking inputs.

## App-Readable Artifact Schema Proposal

Future artifact format should be a single app-readable CSV or JSON produced only by a separately approved sprint.

Required row fields:

- `player_id`
- `player_display_name`
- `position`
- `outcome_status`
- one display-safe field per approved head, using integer percentage text or blank/unavailable:
  - `qb_t12_display_pct`
  - `rb_t12_display_pct`
  - `rb_t24_display_pct`
  - `wr_t12_display_pct`
  - `wr_t24_display_pct`
  - `wr_t36_display_pct`
  - `te_t12_display_pct`
- `unavailable_reason_public`
- `artifact_version`
- `source_evidence_version`
- `generated_at_utc`

Explicitly forbidden app-readable fields:

- raw probability decimals;
- hidden high-precision probabilities;
- ranking/sorting keys;
- rank deltas;
- market/ranking/projection/ADP/trade fields;
- blocked heads;
- model coefficients;
- training labels;
- same-season target stats;
- any field that can be used as a hidden sort key.

## Future File/Path Allowlist Proposal

A later app display-wiring packet, if approved, should be limited to a narrow allowlist such as:

- `docs/outcome_probability/BUILD_SPRINT_5EH_NUMERIC_OUTCOME_APP_DISPLAY_WIRING.md`
- `src/services/nwr_outcome_numeric_probability_display_service.py`
- `tests/test_nwr_outcome_numeric_probability_display_service.py`
- `scripts/outcome_probability/audit_phase10_numeric_outcome_display_static_guard_v1.py`
- `app/pages/05_rankings.py`
- `tests/test_dynasty_rankings_page.py`

Any future generated app-readable artifact path must be proposed and approved separately before creation. Sprint 5EF creates none.

## QA Tests Required Before App Display Wiring

Future QA must prove:

- only approved heads appear;
- `rb_t24` remains present only with the 5EC/5EE audit provenance;
- app-readable artifact has integer percentages only;
- no hidden raw probability fields exist;
- unavailable rows do not display `0%`;
- rookies and kickers remain unavailable;
- no rankings/sorting behavior changes;
- no hidden sort keys are created;
- app page tests verify labels, tooltip copy, and unavailable behavior;
- static guard blocks app-readable generated outputs outside the approved path;
- rollback removes display wiring without changing Rankings sorting.

## Rollback Plan

Rollback for a future numeric display implementation must:

- remove the app-readable artifact from the app load path;
- restore the prior non-numeric Outcome status or placeholder display;
- leave Rankings sorting unchanged;
- run Phase 8/9 static no-leakage guards plus a numeric-display static guard;
- confirm no generated app-readable artifacts remain promoted.

## Recommendation

Verdict: GREEN for Sprint 5EG numeric display implementation readiness verdict.

This sprint approves only readiness assessment for a future implementation packet. It does not approve app display wiring, artifact creation, push, deploy, release, rankings/sorting changes, hidden sort keys, or promoted artifacts.
