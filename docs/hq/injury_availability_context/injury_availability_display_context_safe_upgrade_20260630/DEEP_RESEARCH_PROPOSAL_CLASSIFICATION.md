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
| IAC-04 | Add display-only gates/specs for weekly_rosters, rosters, player_stats, snap_counts, schedules | `SAFE_NOW` for docs/spec; `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` for active data use | This lane adds docs/schema/service prep only. |
| IAC-05 | Compute games_while_rostered | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Requires refreshed weekly roster and schedule coverage. |
| IAC-06 | Compute games_with_snaps and games_with_recorded_stats | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Requires refreshed snap count and player-stat coverage. |
| IAC-07 | Compute games_played_context | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Requires denominator validation across refreshed inputs. |
| IAC-08 | Compute games_missed_while_rostered | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Requires refreshed roster and team-game denominators. |
| IAC-09 | Add per-game denominator labels | `SAFE_NOW` for label/spec; `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` for populated values | Labels and caveats are documented; values remain NEI. |
| IAC-10 | Dynamic season anchors | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Requires refreshed metadata and explicit green health status. |
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
