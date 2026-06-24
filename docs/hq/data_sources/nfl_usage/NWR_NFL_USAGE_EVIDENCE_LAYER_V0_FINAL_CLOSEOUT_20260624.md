# NFL Usage Evidence Layer V0 Final Closeout

## Overall Verdict

GREEN.

The finish lane resolved the prior YELLOW dependency/live-smoke blocker. `nflreadpy` is installed in `.venv`, live field-only smoke ran, live field inventories and schema fingerprints exist, review artifacts were regenerated, validation/quarantine reports are complete, and the optional hidden read-only review page was added.

## Source Families Included

player_stats, pbp, snap_counts, nextgen_stats, participation, ftn_charting, pfr_advstats, rosters, players, and ff_playerids.

## Sources Actually Live-Smoked

2024 live smoke succeeded for player_stats, snap_counts, pbp, nextgen_stats passing/receiving/rushing, participation, ftn_charting, pfr_advstats pass/rush/rec, rosters, players, and ff_playerids.

## Sources Skipped / Quarantined

No source family was skipped. Field-level quarantine applies to blocked raw-source columns such as fantasy point fields and score-state fields.

## Supported True Factual Fields

Supported factual fields include snaps, offensive snap share, targets, carries, receptions, rushing yards, receiving yards, air yards, YAC where present, rushing/receiving/passing first downs, `yardline_100`, player/team/game/week identifiers, and source-specific NGS/PFR/FTN inventory fields for review.

## Derived Proxy Fields

Touches, opportunities, red-zone/inside-10/inside-5 usage derivations remain available in the derivation service. First-downs-per-touch and usage shares remain proxies until backtested. Participation route-like fields remain proxy-only.

## Licensed-Data Gaps

True routes run, true TPRR, true YPRR, and full route assignment/tree context remain licensed-data gaps.

## Blocked / Unsafe Fields

Ranks, projections, ADP, market values, trade values, analyst blurbs, start/sit grades, betting odds, DFS salaries, proprietary scores, RotoWire live scrape data, fantasy points as model/target fields, and score-state fields for this lane.

## Dependency Status

`nflreadpy` was added to `pyproject.toml` and `requirements.txt`, installed into `.venv`, and imported successfully as version `0.1.5`.

## Guardrail Status

- Raw data tracked: no
- Shared/local_exports/runtime tracked: no
- App wiring status: hidden read-only review page only
- Model input status: no
- latest_candidate/latest_approved: untouched
- Frozen board: 66 rows
- Pinned hash: unchanged

## Optional Review Page

Added: `/nfl-usage-evidence-review`

The page reads only committed summary artifacts and does not feed rankings, Drafting Mode, Player Compare, Trading Lab, Post-Draft, or model features.

Browser smoke passed on `/nfl-usage-evidence-review`, `/drafting-mode`, `/rankings`, `/settings-data-health`, and `/unified-universe-review`.

## Remaining Blockers

Only promotion blockers remain: any future display/model use requires the promotion/backtest gate. True route metrics remain licensed-data gaps.

## Recommended Next Step

Run a separate promotion/backtest lane if any specific usage fields should graduate from research-only to display-only candidate or candidate model feature.
