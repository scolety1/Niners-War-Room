# Deep Research Proposal Classification

Source packet: `NWR Injury Availability Display Context Safe Upgrade Lane`

Current source-state interpretation:

- Existing injury-report V0 display is green as review-only app display.
- Merged HQ now includes the player context artifact and the denominator
  display artifact.
- Denominator values are display-only and remain excluded from model/rank/source
  truth paths.

| ID | Proposal | Classification | Implementation Status |
| --- | --- | --- | --- |
| IAC-01 | Preserve current injury source gate | `SAFE_NOW` | Existing `nflreadpy.load_injuries` source gate remains review-only factual context. |
| IAC-02 | Continue V0 display in Rankings Outcome Context and Player Compare | `SAFE_NOW` | Existing display surfaces remain review-only. |
| IAC-03 | Show injury-report counts and caveat | `SAFE_NOW` | Season-total report-week counts are safe factual display context. |
| IAC-04 | Add display-only gates/specs for weekly_rosters, rosters, player_stats, snap_counts, schedules | `SAFE_NOW` | Player Compare displays safe tracked-artifact fields for safe identity rows. |
| IAC-05 | Display games_while_rostered | `SAFE_NOW` | Consumed from tracked denominator artifact for safe rows only. |
| IAC-06 | Display games_with_snaps and games_with_recorded_stats | `SAFE_NOW` | Consumed from tracked denominator artifact for safe rows only; missing remains NEI. |
| IAC-07 | Display games_played_context | `SAFE_NOW` | Factual rostered/snap/stat context only. |
| IAC-08 | Compute games_missed_while_rostered | `YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION` | Still blocked; requires explicit game-status source and must not infer cause. |
| IAC-09 | Add per-game denominator labels | `SAFE_NOW` | Populated only from safe denominator rows. |
| IAC-10 | Dynamic season anchors | `SAFE_NOW` | `season_anchor` is explicit in the tracked denominator artifact. |
| IAC-11 | Use availability in rankings/model/outcome/trade/pick logic | `NEED_MODEL_GATE` | Out of scope for this lane. |
| IAC-12 | Reuse `lve_injury_durability_service.py` scoring outputs | `BLOCKED` | Not imported, called, or reused. |
| IAC-13 | Treat missing injury/availability as healthy/clean/safe | `BLOCKED` | Missing context remains `Not enough information`. |
| IAC-14 | Use scraped/vendor/Gmail/rumor sources | `BLOCKED` | Only approved tracked NFLVerse factual sources are in scope. |

## Identity And Schedule Notes

Rows with `NEED_IDENTITY_REVIEW` or `NEED_IDENTITY_APPROVAL` remain status-only.
Identity recommendations are not approved joins.

Schedule context is safe only as a denominator support source in this lane.
Next-game, opponent, bye, health, matchup, or availability inference remains
gated for a separate lane-specific activation review.
