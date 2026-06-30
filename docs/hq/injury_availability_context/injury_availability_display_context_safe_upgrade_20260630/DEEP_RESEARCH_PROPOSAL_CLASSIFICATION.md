# Deep Research Proposal Classification

Source packet: `NWR Injury Availability Display Context Safe Upgrade Lane`

Current source-state interpretation:

- Existing injury-report V0 display is green as review-only app display.
- Current full-refresh completion gate lists `nflverse pull/status` as `YELLOW`.
- Dataset-dependent availability denominator work remains
  `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN`.

| ID | Proposal | Classification | Implementation Status |
| --- | --- | --- | --- |
| IAC-01 | Preserve current injury source gate | `SAFE_NOW` | Existing `nflreadpy.load_injuries` source gate remains review-only factual context. |
| IAC-02 | Continue V0 display in Rankings Outcome Context and Player Compare | `SAFE_NOW` | Existing display surfaces remain unchanged and review-only. |
| IAC-03 | Show injury-report counts and caveat | `SAFE_NOW` | Season-total report-week counts are safe factual display context. |
| IAC-04 | Add display-only gates/specs for weekly_rosters, rosters, player_stats, snap_counts, schedules | `SAFE_NOW` for tracked direct display fields; denominator computations deferred | Player Compare now displays safe tracked-artifact fields for safe identity rows. |
| IAC-05 | Compute games_while_rostered | `YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION` | Requires approved denominator artifact; not computed in app pages. |
| IAC-06 | Compute games_with_snaps and games_with_recorded_stats | `YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION` | Snap recency/sample is safe; game counts remain deferred. |
| IAC-07 | Compute games_played_context | `YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION` | Last active season/week is safe; exact games played remains deferred. |
| IAC-08 | Compute games_missed_while_rostered | `YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION` | Requires rostered-game denominator artifact and must not infer cause. |
| IAC-09 | Add per-game denominator labels | `SAFE_NOW` for labels/spec; `YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION` for values | Labels and caveats are documented; values remain NEI. |
| IAC-10 | Dynamic season anchors | `YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION` | Requires explicit tracked artifact support. |
| IAC-11 | Use availability in rankings/model/outcome/trade/pick logic | `NEED_MODEL_GATE` | Out of scope for this lane. |
| IAC-12 | Reuse `lve_injury_durability_service.py` scoring outputs | `BLOCKED` | Not imported, called, or reused. |
| IAC-13 | Treat missing injury/availability as healthy/clean/safe | `BLOCKED` | Missing context remains `Not enough information`. |
| IAC-14 | Use scraped/vendor/Gmail/rumor sources | `BLOCKED` | Only approved NFLVerse factual sources are in scope. |

## `ALREADY_DONE`

The existing V0 injury-report display lane already provides:

- Review-only injury context in Rankings Outcome Context.
- Review-only Injury / Availability Context in Player Compare.
- Explicit no-model-input and no-rank-mutation labels.

This lane preserves those behaviors rather than rewiring them.

## Rerun Activation

The merged NFLVerse player context artifact allows direct display of roster status,
weekly roster status, injury report status, practice status, injury report date/week,
last active season/week, snap recency/sample size, age source, and identity caveat
for the 240 safe identity rows.

Rows with `NEED_IDENTITY_REVIEW` remain status-only.
