# Entry Status Policy

## Scope

This policy is review-only for 2000-2024 QB/RB/WR/TE historical rookie entry-status hygiene. It
consumes the prior backfill-policy packet at `docs/hq/rookie_model/rookie_model_historical_cfbd_and_outcome_backfill_policy_20260630/` and does not rewrite its CFBD,
Outcome V2, feature, or leakage policies.

## Evidence Hierarchy

1. `drafted`: public nflverse/nflreadpy draft-pick row with draft year, round, pick, team, and
   player identity context.
2. `confirmed_udfa`: reserved for a future source-approved UDFA/NFL-entry source plus a verified
   not-drafted lookup in the same class. This artifact creates zero confirmed UDFA rows.
3. `likely_udfa_needs_review`: player registry has `rookie_season` in 2000-2024, no registry draft
   capital, and no draft-pick ID match. This is a candidate status only.
4. `free_agent_rookie_needs_review`: first-time NFL entrant evidence exists, but rookie/UDFA status
   is unclear. Player-stats-only evidence may support this in a future gate; this artifact does not
   create clean free-agent rookie rows.
5. `wrong_universe`: evidence shows the player is outside the 2000-2024 rookie universe.
6. `name_collision`: same-name, position mismatch, duplicate ID, or conflicting identity evidence.
7. `unknown`: default when evidence is insufficient.

## Required Fields

Drafted rows require player name, position, rookie class/draft year, draft round, pick, team, and
at least one identity key when available. Non-drafted review candidates must keep draft fields as
`Not enough information`; no zero or fake values are allowed.

## Blocked Assumptions

- Absence from draft-pick data does not prove confirmed UDFA.
- A player not found in draft picks may still be a wrong-universe player, identity collision, or
  non-rookie free agent.
- Fake round 8 is prohibited because it fabricates draft capital and hides source uncertainty.
- `draft_round=0`, `overall_pick=0`, and `draft_pick=0` are prohibited.
- Missing values must be blank/unknown/`Not enough information`, never zero/false/clean/healthy.

## Use By Rookie Outcome

Rookie Outcome may use this artifact only to evaluate coverage and propose future gates. It may not
train, tune, rank, or promote UDFAs from this file. Drafted-only work must remain explicitly
drafted-only. Unknown, wrong-universe, and name-collision rows are blocked from training.

Outcome V2 labels and future NFL production cannot prove entry status because they occur after the
entry decision date and would convert outcomes into source identity evidence.
