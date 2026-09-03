# Historical row → RankingResult field map (section 2)

Mechanical inspection of `src/services/redraft_engine_v1_service.py`'s
`ProjectionPlayer`, `ProjectionSnapshot`, `generate_rankings()`, and
`RedraftRankingRow`. The bridge (`historical_ranking_bridge_service.py`)
does **not** build a second scoring engine — it constructs a real
`ProjectionSnapshot` from historical rows and calls the real,
unmodified `generate_rankings()`, the exact function a live draft uses.
Every derived field below (`replacement_points`, `tier`, `confidence`,
`starter_gap`, ...) is therefore computed by production code, not
re-derived here.

## ProjectionPlayer (input side)

| Current field | Historical source field | Required/Optional | Point-in-time requirement | Default policy | Missingness policy | Leakage risk |
|---|---|---|---|---|---|---|
| `player_id` | `player_id` | Required | n/a | none | row excluded if absent | none |
| `player_name` | `player_name` | Required | n/a | none | row excluded if absent | none |
| `position` | `position` | Required | as of `draft_date` | none | row excluded if absent | historical position, never current |
| `team` | `team` | Required | as of `draft_date` | none | row excluded if absent | historical team, never current |
| `season` | `season` | Required | n/a | none | row excluded if absent | none |
| `source_status` | fixed `"imported_real_data"` for every row that has real stat components | Required | n/a | fixed constant | n/a | none |
| `evidence_status` | fixed `"HISTORICAL_REPLAY_IMPORT"` | Required | n/a | fixed constant | n/a | none |
| `source_as_of` | `projection_as_of` (falls back to `draft_date`) | Required | must be `< draft_date` (existing leakage validator already enforces this upstream) | none | row excluded if absent | **HIGH if wrong** — this is the exact field the leakage gauntlet checks |
| `rookie` | `rookie` column if present, else `False` | Optional | n/a | `False` | never inferred from name/round | low — a wrong default only mis-labels a veteran as non-rookie, doesn't leak outcome data |
| `stats` (passing_yards, rushing_yards, receptions, ... — the exact keys `score_projection()` reads) | new optional stat-category columns this bridge defines (`PROJECTION_STAT_FIELDS`), OR `projected_points_override` for K/DST | Required to produce a scored row | as of `projection_as_of` | **none — never fabricated** | **player EXCLUDED from the snapshot entirely, never scored as 0** | HIGH if these were ever back-filled from realized stats instead of a genuinely pre-draft projection — never done here |

`draft_day_prior_override` is left at its default (`False`) — this field
is specifically for the live 2026 KHA draft-day freshness bypass, not a
historical replay concept.

## RedraftRankingRow (output side)

Every field below is computed by the real `generate_rankings()` from the
`ProjectionPlayer`s above — nothing here is written by the bridge
directly:

| Field | Historically reconstructable? |
|---|---|
| `overall_rank`, `position_rank`, `tier`, `position_tier`, `overall_tier_label`, `position_tier_label` | Yes — computed from the real scored/ranked set exactly as in production |
| `projected_points`, `replacement_points`, `replacement_adjusted_value`, `starter_gap` | Yes — computed by `score_projection()`/`calculate_replacement_levels()` on the reconstructed stats |
| `confidence` | Yes — computed by the same `_confidence()` heuristic production uses |
| `player_id`/`player_name`/`position`/`team`/`source_status`/`evidence_status`/`source_as_of`/`rookie` | Passed through from `ProjectionPlayer` |
| `profile_id`/`profile_name` | From the caller-supplied historical `LeagueProfile` |
| `authority_label`, `model_family` | Unchanged constants — same production defaults |

## Fields the RankingResult side does NOT carry, but the directive also asks the bridge to preserve

These live outside `RankingResult` and are built as a companion
`PointInTimeFeatureStore` + `AdpSnapshot` by the same bridge call, not
inside `RankingResult` itself (production doesn't carry them there
either — Draft Room gets ADP/market data from a separate `AdpSnapshot`
today):

| Concept | Where it lives in the bridge output | Missingness policy |
|---|---|---|
| Market information (platform ADP) | `AdpSnapshot` built from `platform_adp`/`adp_as_of` | player omitted from `entries`, listed in `unmatched` if absent |
| Availability/status | `PointInTimeFeatureStore` (`FAMILY_AVAILABILITY`) from `status_as_of` | `UNKNOWN` FeatureValue if absent — never a fabricated "ACTIVE" |
| Feature provenance / source_as_of / model version context | Every `FeatureValue.provenance_hash`/`source_as_of`/`feature_version`, and `HistoricalRankingBridgeResult.bridge_version` | n/a — always present by construction |

## Where production code assumes a field always exists

`generate_rankings()` requires every position with `required[position] >
0` to have at least `required + 1` scored players (an "insufficient
universe" check) — this is an EXISTING production guarantee, not
weakened here. A historical season whose real archive is too thin for a
league's roster requirements will legitimately hit this same guardrail
and return `RankingResult.errors` non-empty (handled: option **C**,
block that replay case) — never bypassed to force a result.
