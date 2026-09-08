# NWR Prospective 2026 Freeze (2026-09-08, post-403-draft overnight pass)

**Verdict: `FROZEN_REFERENCE_ENGINE_UNCHANGED_NO_CHALLENGER_ADOPTED`**

No challenger evaluated during this session's post-draft overnight program
(`fc6c180d`..`d815c633`, plus the pre-draft pass `249481d0`) was adopted as
the new default. Every backend addition this session is an explicit,
opt-in, additive function that changes nothing for an existing caller.
This document freezes the reference engine's exact versions and evidence
state as it stands at `d815c633`, before any real 2026 season outcome is
observed, so future evaluation can be genuinely prospective rather than
retrospectively fitted.

## Why nothing was adopted

Per this program's own explicit rule ("preserve the reference until a
challenger earns adoption") and the historical-tuning discipline already
established for this project (2016/2024/2025 all burned, no pristine
historical holdout remains, "no re-opening a burned holdout"): every
challenger built this session was validated only against the ONE real
403 N 18th draft's 14 owner decisions plus synthetic/isolated-league
tests -- real, useful evidence for root-causing and for proving a
mechanism works as designed, but not the external-outcome-scored,
multi-draft, walk-forward evaluation adoption would require. Adopting
any of them now would be exactly the "tune to make one draft's choices
look right" behavior this whole program was explicitly told not to do.

## Frozen component versions

| Component | Version / identity | Status |
|---|---|---|
| Player Score / RAV | `replacement_adjusted_value` via `score_projection` (`redraft_engine_v1_service.py`) | UNCHANGED |
| Team Score | `shadow-team-score-v1` | UNCHANGED (default call; `impact_hypotheses=()`) |
| Championship Equity | `shadow-championship-equity-v1` | UNCHANGED (default call; `impact_hypotheses=()`) |
| Pick Score | `shadow-pick-score-v1` (`RESEARCH_ONLY_PICK_SCORE`) | UNCHANGED |
| Decision policy | Pick-Score-descending sort, top row = recommendation | UNCHANGED |
| Recommendation candidate universe | `diversify_candidate_shortlist` + the forced-position union fix (commit `a7860e39`, prior pass) | UNCHANGED this session |
| Projection snapshot | `NWR_REDRAFT_2026_VETERAN_PLUS_ROOKIE_COMBINED_V1`, sha256 `e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25`, veteran component `source_as_of=2026-08-08`, rookie component `source_as_of=2026-07-30` | UNCHANGED VALUES; freshness-gate access restored via a scoped, veteran-only, time-limited `DRAFT_DAY_AUTHORIZATION.json` (issued this session, expires `2026-09-09T10:00:00Z`) |
| Status/risk taxonomy | `ai_intelligence_backend_service.NEWS_EVENT_TYPES` / `_DIRECT_IMPACT_RULES` | EXTENDED this session (PUP_NFI, ADMINISTRATIVE_EXEMPT, RELEASED added) -- additive, no existing rule changed, still has zero real ingested events |
| Market source (403 N 18th) | ESPN — Owner Snapshot — 2026-09-07, 276/294 matched | UNCHANGED |
| K/DST manual assets (403 N 18th) | 153 real assets, reused unmodified | UNCHANGED |

## Real evidence this freeze carries forward (not retuned on)

- Full 14-pick real 403 replay + counterfactual (recommendation changed
  in 9/14 turns under the untested `marginal_roster_utility` challenger;
  see `nwr-post-draft-engine-forensics-v1` memory for the full table).
- Age/experience bias: a real, prior (2026-07-21) historical study
  rejects the "NWR undervalues youth" hypothesis -- the measured bias, if
  anything, runs the opposite direction (older cohorts under-predicted,
  younger cohorts over-predicted), and a correction candidate for THAT
  bias was already tested and rejected for failing broader validation
  gates. Not reopened.
- Make-It-Back calibration against the real completed 403 board:
  back-to-back turns exactly calibrated (1.000 predicted, 1.000 actual,
  n=45); partial-round gaps show a modest real under-prediction (0.500
  predicted vs 0.595 actual, n=42) -- not acted on, sample too small to
  justify a change against the existing baseline.
- Multi-league mock battery (8/10/12/16-team + Superflex): all 5 shapes
  completed cleanly under the CURRENT unchanged reference engine, K/DST
  always exactly 1 each at rounds 15/16, QB count scaling sensibly
  (1/2/2/2/3) with real scarcity -- the frozen baseline's fundamentals
  are sound.

## Prospective evaluation protocol (going forward, before any outcome accrues)

1. Record this document's commit (`d815c633`, or later if this freeze is
   re-cut) as the reference point.
2. When 2026 season results become available, compare REALIZED points
   against the projection snapshot frozen here (`source_as_of=2026-08-08`
   veterans / `2026-07-30` rookies) -- an honest, prospective, walk-forward
   comparison, not a retrospective refit.
3. Any future challenger (marginal_roster_utility, the status/risk
   partial-discount tier, FFA-as-ensemble, etc.) must be evaluated against
   REAL weekly outcomes once available, using the same registered-metric
   discipline (MAE, Spearman, decision regret, roster-construction
   pathology counts) already used for this project's historical program --
   never against how well it would have justified the owner's own real
   403 picks in hindsight.
4. Do not retune Player Score / Team Score / Championship Equity / RAV /
   Pick Score based on a single draft's outcome, regardless of how the
   403 team performs this season.

## Real limitations disclosed, not fixed, carried into 2026

- No facade/UI path exists to ingest a real owner-supplied news event
  (the wired `impact_hypotheses` plumbing has nothing feeding it).
- `marginal_roster_utility`'s universal bench-redundancy decay doesn't
  distinguish QB's low real backup-utilization rate from RB/WR's higher
  one (found via the 12.01 counterfactual).
- No Ballers/UDK K/DST reference exists (the owner's only real UDK export
  has zero K/DST rows).
- No PDF ingestion pipeline exists (no owner-owned PDF sample to build
  or validate one against).
- FFA Sept-4 vs NWR Aug-8 comparison done; ensemble/replacement decision
  NOT made.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SVeKhFHk5pYE5iRihLvFxy
