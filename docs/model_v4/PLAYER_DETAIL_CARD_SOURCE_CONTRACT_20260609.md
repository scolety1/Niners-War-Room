# Player Detail Card Source Contract - 2026-06-09

## Purpose

Define one source-safe player-card contract for Rankings, Draft Prep, Live Draft Room, and future Roster Decisions. The card is a review surface. It must not create private value, tune formulas, mutate draft state, or produce final roster/draft actions.

## Common Schema

Every page should pass a normalized dictionary with these common fields when available:

| Field | Meaning | Missing behavior |
| --- | --- | --- |
| `player` | Display player name | `-` |
| `position` | Football position | `-` |
| `age` | Player age | `-` |
| `team` | Current/display NFL team | `-` |
| `roster_status` | MY TEAM, AVAILABLE, OTHER TEAM, UNKNOWN, etc. | `UNKNOWN` |
| `source_type` | rookie, free_agent, current_player, scouting_pool, etc. | `unknown` |
| `nwr_score` | Relevant source-safe NWR value for the page | blank if unavailable |
| `nwr_rank` | Relevant source-safe NWR rank for the page | blank if unavailable |
| `trust_status` | Scored, Scored + Warnings, Capped Score, Source Repair Needed, etc. | `Trust unknown` |
| `warning_summary` | Human-readable compact warnings | `No active warning` |
| `data_needed` | Human-readable missing/source data | `-` |
| `market_rank_display_only` | Market/startup context only | blank if unavailable |
| `league_rank_display_only` | League rank context only | blank if unavailable |
| `source_path` | Source receipt path | collapsed receipts only |
| `source_column` | Source receipt column | collapsed receipts only |
| `lineage_class` | Source/model lineage | collapsed receipts plus trust badge if important |
| `allowed_use` | What the row may be used for | collapsed receipts; summarized if restrictive |
| `blocked_use` | What the row may not be used for | collapsed receipts; summarized if restrictive |
| `legacy_comparison_score` | Legacy active-pack score, if present | comparison-only disclosure |
| `notes_context_tags` | User notes, prior-history tags, status tags | context-only |

## Common Rules

- Missing numeric values stay blank or `-`; never backfill from market, league, prior draft history, RotoWire projection/ranking fields, legacy active-pack scores, or public sources.
- `market_rank_display_only` and `league_rank_display_only` may be shown only as display context.
- `legacy_comparison_score` is comparison-only. It cannot drive score, rank, tier, trust, outcome, draft fit, or recommendations.
- `allowed_use` and `blocked_use` must be preserved in receipts.
- Raw source receipts are collapsed by default.
- The card must avoid final action language: no `Draft this player`, `Target`, `Buy`, `Sell`, `Cut`, `Defer`, or start/sit commands.
- User notes and context tags cannot alter private score.

## Rankings Extension

Rankings may pass:

- `nwr_dynasty_score`
- `nwr_dynasty_rank`
- `score_status`
- `confidence_cap`
- `confidence_status`
- `market_rank`
- `market_rank_source`
- `nwr_vs_market`
- `league_rank`
- `league_rank_source`
- `nwr_vs_league`
- `risk_level` only if source-safe or clearly legacy/display-only
- `outcome_status`
- `outcome_fields`
- `raw_model_warning_flags`
- `team_resolution_status`
- `canonical_team_source`
- `raw_source_repair_notes`

Rankings-specific blocked uses:

- Market, league, ADP, startup, consensus, projections, trade calculators, and legacy scores cannot affect NWR Dynasty Score, rank, trust, risk, tier, or outcomes.
- Outcome percentages remain blank/in development unless a real private model exists.

## Draft Prep Extension

Draft Prep may pass:

- `pick_window`
- `fit_band`
- `draftable_status`
- `legal_draftable`
- `protected_status`
- `rookie_status`
- `free_agent_status`
- `dropped_veteran_status`
- `manual_status`
- `nwr_draft_value`
- `nwr_rookie_score`
- `expected_league_slot_context`
- `nwr_slot_context`
- `value_threshold_context`
- `prospect_talent_context`
- `landing_spot_context`
- `draft_capital_context`
- `role_path_context`
- `historical_user_context_tags`
- `legal_pool_status`

Draft Prep-specific rules:

- Scouting-prep rows are not confirmed legal draftables unless the legal source proves it.
- Dropped/released veterans remain pending until the source file is supplied.
- Prior draft history and spreadsheet highlights are display-only context.
- Yellow highlight means `Must Review At Cost`, not draft at any cost.
- `2026 5.04` remains `No Baseline`, `Manual Watchlist`, and no exact equivalence.

## Live Draft Room Extension

Live Draft Room may pass:

- `drafted_status`
- `drafted_pick`
- `selected_pick`
- `current_pick`
- `pick_owner`
- `hide_drafted`
- `best_remaining_rank`
- `mock_live_state_context`
- `legal_pool_pending_status`
- `session_state_key`
- `remaining_pool_status`

Live Draft Room-specific rules:

- Draft state is session/local mock state only.
- Source data packs are read-only.
- Legal pool pending copy must remain visible until dropped/released veteran data is supplied.
- Best remaining is scouting/mock context, not final draftability.

## Future Roster Decisions Extension

Future Roster Decisions may pass:

- `roster_pressure`
- `pressure_reason`
- `forced_drop_rule_context`
- `owner_team_status`
- `replacement_context`
- `cut_cost_context`
- `roster_deadline_context`
- `decision_review_status`

Roster Decisions-specific rules:

- The card may explain pressure and roster rules, but it must not issue final keep/cut/trade/drop commands.
- Decision Board remains blocked from this task.

## Sentinel Requirements

- Keenan Allen legacy active-pack `private_score = 82.4` remains comparison-only.
- Darius Slayton legacy active-pack `private_score = 78.88` remains comparison-only.
- `2026 5.04` remains no-baseline/manual watchlist/no exact equivalence when relevant.
- Outcome percentages remain blank/in development unless a real private outcome model exists.

