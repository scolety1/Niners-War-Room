# Guardrails And Non-Goals

Verdict: `YELLOW_GUARDRAILS_CONFIRMED_NO_ACTIVATION`

## Global Guardrails

- Do not build substrate artifacts in this packet.
- Do not train models.
- Do not tune models.
- Do not run model experiments.
- Do not create probabilities.
- Do not approve model use.
- Do not approve training use.
- Do not approve source-truth promotion.
- Do not wire app behavior.
- Do not approve Rookie Gate G.

## Protected Product Areas

This packet must not change:

- app files;
- Rankings behavior;
- Player Compare behavior;
- Trading Lab behavior;
- Development Lab behavior;
- Draft Room or Mock Draft behavior;
- Injury/Availability UI;
- Outcome V2 probabilities;
- Rookie probabilities;
- source truth;
- model outputs;
- ranks, tiers, or hidden sort;
- `latest_candidate` or `latest_approved`;
- frozen board;
- pinned snapshots;
- runtime JSON;
- trade value;
- pick value;
- recommendations.

## Source And Data Guardrails

- Do not track raw/shared/cache/local_exports/secrets/vendor/Gmail/private files.
- Do not treat display rows as experiment rows.
- Do not treat current player context as a historical feature panel.
- Do not read or write blocked source truth for this packet.
- Do not promote any builder artifact to source truth.
- Do not use `ff_rankings`.
- Do not approve CFBD model/training input.
- Do not approve UDFA modeling.

## Missingness Guardrails

- Missing values remain `Not enough information`.
- Missing draft capital is not confirmed UDFA.
- Missing availability is not healthy, clean, no-risk, played, or missed.
- Missing injury context is not healthy.
- Missing depth context is not no-role.
- Missing snap context is not zero usage.
- Missing stat context is not zero production.
- Missing schedule context is not clean or favorable.

## Context Guardrails

- Schedule context is not recommendation, matchup strength, start/sit, playoff odds, or trade timing.
- Injury context is not injury risk, durability, medical projection, or comeback projection.
- Contract context is not trade value or player value.
- Player stats sidecars are not label truth, model input, training truth, or source truth without a separate later HQ gate.
- Labels are evaluation targets only and are never input features.

## Gate Posture

- Gate E remains review/R&D only.
- Gate F remains partial display/review only where already separately approved.
- Gate G remains blocked.

## Non-Goals

- No artifact rebuild.
- No app integration.
- No source-truth promotion.
- No runtime data update.
- No candidate or approved snapshot update.
- No probability, rank, hidden sort, valuation, or recommendation change.
