# Draft Repository Findings

## Decision

Keep NWR's league-specific Redraft Champion engine. Adapt domain patterns from `zacharykirby/ai-nfl-fantasy-draft`; adapt calibrated opponent/availability concepts from `joewlos/fantasy_football_monte_carlo_draft_simulator`. Do not replace NWR with either repository.

## Best architecture

The Zachary Kirby repository cleanly separates immutable board facts, mutable session state, deterministic recommendation and optional model explanation. Its event-backed selections, snake ownership, every-team rosters, atomic autosave, undo/recovery, duplicate checks, tier cliffs, position runs and next-pick survival address NWR's exact Redraft state gaps. Its MIT license permits later reviewed reuse, but NWR should implement its own provider/storage contracts first.

## Best mock/availability logic

The Joe Wlos repository trains positional selection likelihood from historical league drafts with logistic regression and simulates full rosters/outcomes. The reusable idea is a calibrated opponent distribution, not its codebase or one universal league model. NWR Phase 1 should begin with seeded ADP distributions and roster construction; historical league calibration is an optional later increment after sample-size and backtest gates.

## Target split

- Board truth: NWR projections, league scoring, replacement value, confidence.
- Market timing: governed ADP snapshot and dispersion.
- Session truth: immutable event log projected into board, rosters and current pick.
- Recommendation: NWR value + roster need + tier cliff + make-it-back estimate.
- CPU: ADP/history distribution + roster constraints; never NWR rank.
- Explanation: deterministic evidence packet; optional language model may explain but not mutate or choose unavailable players.
