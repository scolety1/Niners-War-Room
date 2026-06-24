# NFL Usage Evidence Layer V0 Report

## Verdict

YELLOW. V0 evidence infrastructure is complete as a safe research lane, but live field introspection and live source sampling are blocked until `nflreadpy` is approved and installed in the project environment.

## What Was Built

- Source contract, allowlist, blocklist, source inventory, and field inventory plan.
- Fail-closed core loader service for snap counts, player stats, and pbp.
- In-memory derived usage service for touches, opportunities, red-zone, inside-10, inside-5, and first-down role indicators.
- Advanced/context source inventory for NGS, participation, FTN charting, and PFR advanced stats.
- Validation, quarantine, and schema fingerprint services.
- Sanitized review artifacts and reports.
- Promotion gate and backtest design.
- CFBD parking-lot doc for a separate College/Rookie Evidence Layer.

## Included Source Families

- player_stats
- pbp
- snap_counts
- nextgen_stats
- participation
- ftn_charting
- pfr_advstats
- rosters/player IDs/crosswalks

## Supported True Factual Fields

Core factual fields include snaps, offensive snap share, targets, carries, receptions, rushing yards, receiving yards, receiving air yards, YAC when present, rushing first downs, receiving first downs, passing first downs, season/week/game/team/player identifiers, and pbp `yardline_100`.

## Derived Proxy And Derived Fact Fields

Transparent derived facts include touches, opportunities, red-zone carries/targets/touches, inside-10 carries/targets/touches, inside-5 carries/targets/touches, rushing first downs, and receiving first downs when source event flags are present.

Proxy fields include first downs per touch and team-week red-zone/inside-10/inside-5 shares until backtested. Route participation, TPRR-like, and YPRR-like fields are proxies unless exact route-run denominators are verified.

## Licensed-Data Gaps

- True routes run
- True TPRR
- True YPRR
- Full route assignment/tree context not present in approved public structured sources

## Blocked Fields

Ranks, projections, ADP, fantasy points as a model/target feature, fantasy values, trade values, market values, start/sit grades, analyst blurbs, betting odds, DFS salaries, proprietary scores, RotoWire live scrape data, and any blocked vendor scrape payload.

## RotoWire Status

RotoWire live collection remains blocked. The only safe future path is manual licensed/user export handling under a separate contract, and even then no rankings, projections, values, or analyst-opinion fields may become model input.

## Display-Only Later

Core factual usage summaries may become display-only candidates after live source introspection, stable schema fingerprints, coverage checks, and attribution pass. V0 does not app-wire them.

## Model Use Later

No V0 field is model input. Candidate model features require the promotion gate and walk-forward backtest design in this folder.

## Exact Next Gate

Approve dependency workflow for `nflreadpy`, run a tiny field-only smoke to shared cache, regenerate field inventories with schema fingerprints, and keep all outputs review-only.
