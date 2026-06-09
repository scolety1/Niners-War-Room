# RotoWire Next Patch List

Date: 2026-05-17

## Current State

The RotoWire intake spine, stats-first review layer, replacement/VORP review
layer, and review-only dynasty candidate layer are working and tested. They are
not enough for roster decisions yet.

The current review-only stats-first output is:

`local_exports/model_v4/rotowire_stats_first/latest/rotowire_stats_first_value_rows.csv`

The named-player review extract is:

`docs/model_v4/ROTOWIRE_STATS_FIRST_NAMED_REVIEW.csv`

The latest RotoWire dynasty candidate output is:

`local_exports/model_v4/rotowire_dynasty_candidate/latest/rotowire_dynasty_candidate_rows.csv`

The latest dynasty candidate audit outputs are:

- `docs/model_v4/ROTOWIRE_DYNASTY_CANDIDATE_NAMED_REVIEW.csv`
- `docs/model_v4/ROTOWIRE_DYNASTY_CANDIDATE_SANITY_REVIEW.csv`

## Why This Is Not Final Yet

The RotoWire layer is intentionally review-only football evidence. It does not
yet fully answer dynasty roster value because it still lacks:

- RB fragility/workload-risk refinement
- WR elite stability / target-earner prior review
- current depth-chart role interpretation
- sourced injury risk severity
- incoming rookie/prospect prior
- roster decision rule lane
- external audit after candidate-layer integration

## Confirmed Good News

- Bijan Robinson and Jahmyr Gibbs rise to the top after format correction.
- De'Von Achane is RB5 in the candidate layer and no longer resembles a legacy
  `bubble` player.
- QBs and TEs are suppressed for 10-team 1QB/no-TE-premium.
- Projections are not used for core value.
- Market/ADP/rankings context is not used for private value.
- Incoming rookies with no NFL evidence are weak/review.
- QB role usage is `not_applicable`, not a false missing-data penalty.
- RotoWire route metrics are available from the licensed local export path.
- First-down-aware replacement/VORP is implemented in review-only form using
  2022-2024 direct nflverse first-down history to estimate 2025 first downs.
- Deep Research supports changing the model target from raw value to
  league-adjusted VORP/replacement value before app promotion.
- Age/dropoff caps now keep older veterans from riding historical production
  above young elite RB/WR assets without review.

## Known Review Findings

These are not necessarily bugs. They are the next formula/audit targets:

| Finding | Likely cause | Next action |
| --- | --- | --- |
| Malik Nabers is outside the high WR sanity tier | Candidate layer is evidence-led and may be missing rookie/prospect or elite-stability context | Inspect receipts before any formula patch |
| BTJ and Luther Burden remain lower than user expectations | Current RotoWire role/stat evidence may not yet capture full dynasty prior | Audit receipts and roster decision lane separately |
| Lamar Jackson may be a sell-high/trade-review case | 10-team 1QB replacement/VORP suppresses QB value while his dynasty premium depends on rushing separation entering the age-risk window | Add QB rushing age-cliff and trade-review fixture before any roster decision gate |
| First-down-aware VORP depends on estimates | RotoWire player stats do not expose direct 2025 first-down fields; estimates use 2022-2024 nflverse history | Audit estimation effects before promotion |
| Incoming rookies have weak review values | No NFL stat history | Build rookie/prospect evidence layer from user uploads |
| Injured/questionable players get review confidence | Sourced injury context exists | Add injury severity mapping; do not treat absence as healthy proof |

## Next Safe Patch Sequence

1. Run external audit against the first-down-aware review-only packet.
2. Add QB rushing age-cliff / sell-high review fixture, with Lamar Jackson as
   the named control.
3. Add rookie/prospect prior intake from `rookie_manual/incoming`.
4. Audit Malik Nabers, BTJ, Luther Burden, and other WR review names against
   receipts before changing weights.
5. Add RB first-down/opportunity/workload-fragility audit before changing
   weights.
6. Add injury severity mapping; keep unsourced health out of value.
7. Produce a neutral external audit packet for the RotoWire candidate layer.
8. Only then consider shadow app promotion.

## Stop Conditions

Stop and audit before app promotion if:

- Achane still looks like a low-confidence/bubble asset without receipt support.
- BTJ/Luther/Chase Brown top-five release logic leaks into Dynasty Asset Value.
- QBs or TEs jump core RB/WR assets without format/receipt justification.
- Market, ADP, or rankings affect private football value.
- Incoming rookies receive strong confidence without sourced prospect evidence.
