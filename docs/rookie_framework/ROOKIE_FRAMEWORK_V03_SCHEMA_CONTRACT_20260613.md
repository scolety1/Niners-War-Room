# Rookie Framework v0.3 Schema Contract - 2026-06-13

## Purpose

This contract defines the source-safe schema rules for the Rookie Framework v0.3 path. It is a tracked documentation checkpoint for future rookie review-board and shadow ranking export work.

This contract does not create rankings, probabilities, bands, app-readable rookie outcome columns, production scoring, private-score replacements, formulas, Streamlit changes, or veteran outcome-head integration.

## League Context

- League format: 10 teams, dynasty/keeper hybrid.
- Scoring context: 1QB, no superflex, no PPR, no TE premium, first downs matter.
- FLEX eligibility: RB/WR/TE only.
- Draft context: 5 rounds including rookies, legal free agents, dropped/released veterans, and manual adds.
- Known picks: 2026 1.03, 1.04, 2.04, 2.08, 5.04.
- Final legal pool remains pending until Roster Declaration Day.

## Current State

Rookie v0.3 is review-only. It may support evidence review, source provenance, manual flags, pick-zone context, and local-only audit exports. It may not be promoted to active rankings, private scores, production formulas, app display, rookie probabilities, rookie bands, or veteran outcome heads.

The committed morning review checkpoint at `289ba738716764a46e22309d1c3448581680c375` remains the current narrative state reference.

## Source-Safety Rules

- Preserve factual, source-safe structured data separately from scouting prose, charting excerpts, injury notes, and market/ranking/projection context.
- Do not infer missing values.
- Do not convert scouting prose into numeric grades.
- Do not use market, ranking, projection, consensus, ADP, or draft-kit material as private-value evidence.
- Do not treat secondary charting as hard private evidence unless a future source hierarchy gate explicitly permits it.
- Keep injury evidence manual or soft unless a future gate defines a source-safe hard concern policy.
- Preserve source caveats and conflicts in review outputs.
- Keep local exports read-only unless a task explicitly approves a rookie-local export update.
- Do not create app-readable outputs unless a future HQ approval and release gate explicitly permits them.
- Do not force rookies through veteran threshold probability services or veteran outcome heads.

## Allowed Evidence Statuses

- `use_now`: Source-safe factual evidence that may be carried into review artifacts under this contract. This does not mean production scoring is approved.
- `use_as_soft_flag`: Evidence that may inform manual review context but cannot open pick zones, override caps, or become private value by itself.
- `manual_review_only`: Evidence requiring human review before any future promotion or schema change.
- `unavailable`: Field was checked or expected but no source-safe value is currently available.
- `excluded`: Field or source is explicitly disallowed for private-value use.
- `conflict_review`: Evidence exists but conflicts or source ambiguity require review before use.

## Allowed Source Types

- `official_structured`: Official team, NCAA, school, conference, or comparable structured factual data.
- `official_note`: Official source note that is factual but not structured enough for automatic hard use.
- `CFBD_structured`: CollegeFootballData-style structured college production or team context.
- `RotoWire_factual`: Factual rows or notes only; no RotoWire rankings, projections, outlooks, values, or market framing.
- `secondary_structured_soft_flag`: Secondary charting or analytical figures retained only as soft flags unless a future gate changes the policy.
- `secondary_note_manual_only`: Scouting or analysis prose retained only for manual review.
- `wire_note_manual_only`: News or injury note retained only for manual review.
- `manual_scouting_only`: Human scouting note retained as qualitative review context only; no numeric conversion.
- `unavailable`: No acceptable source found.
- `excluded`: Source is prohibited or unusable for the field.

## Prohibited Sources As Private-Value Evidence

The following are prohibited as private-value, scoring, ranking, cap-opening, probability, band, or app-output evidence:

- ADP
- public rankings
- consensus
- projections
- fantasy forecasts
- trade calculators
- market values
- draft-kit ranks
- league rank
- prior league draft history
- RotoWire rankings/projections
- legacy `private_score`

If prohibited terms appear in URLs, source names, or source pages, they must remain quarantined from private-value promotion. Their presence must be disclosed as source-context caveats when relevant.

## Pick-Zone Labels

- `1.03_review`: Premium-pick review context for the 1.03 slot. Empty is allowed and may be the correct bust-avoidance state.
- `1.04_review`: Premium-pick manual-review context for the 1.04 slot.
- `2.04_review`: Second-round review context for the 2.04 slot.
- `2.08_review`: Second-round review context for the 2.08 slot.
- `5.04_watch`: Late-pick watchlist or asymmetric dart context.
- `manual_review`: Player/field requires human review before any further promotion.
- `capped`: Player/field is blocked by a hard cap.
- `unavailable`: Player/field lacks source-safe evidence.

Pick-zone labels are review context only. They are not rankings, values, draft recommendations, probabilities, or bands.

## Tag Categories

- WR route earning
- WR separation/press
- WR YAC/contested/drop
- RB contact
- RB first-down/short-yardage
- RB receiving/special teams
- RB pass protection/fumble
- injury
- TE exception
- QB exception
- source conflict

Tags may describe why an item is in review. Tags do not create final rank, private score, production formula input, probability, or band output.

## Manual-Review Reasons

Manual review is required when:

- evidence is soft, secondary, prose-based, injury/news based, or manually scouted;
- a source contains forbidden market/rank/projection context that must be quarantined;
- a premium pick depends on unresolved source-safe evidence;
- a player has injury uncertainty, recurrence ambiguity, or return-status uncertainty;
- a QB/TE exception claim depends on non-structured or low-confidence evidence;
- a field is missing but would materially affect a pick-zone review;
- evidence conflicts across sources or identity matching is uncertain;
- any data collection would require inference.

## Hard Caps Vs Soft Flags

Hard caps block or preserve a capped state until a future approved process changes them. Examples include non-rushing QB profile in 1QB, TE athleticism without target command, athleticism/speed without earning proof, job-security concern on QB rushing exceptions, and source-safety blockers.

Soft flags are review context only. They may highlight possible earning, contact, first-down, receiving, special-teams, injury, or exception evidence, but they cannot:

- open 1.03;
- promote 1.04 from review to recommendation;
- create a final ranking;
- override a hard cap;
- become private value by themselves;
- create probabilities or bands;
- create app-readable outputs.

## Promotion Gates Before Future Production Use

No future rookie production use is allowed unless all of the following occur in order:

1. A review-board export gate approves source-safe review outputs only.
2. A shadow ranking export gate approves a non-production, non-app, review-only shadow artifact.
3. An adversarial audit verifies source safety, row counts, no contamination, no private-score changes, no probability/band creation, and no veteran outcome-head usage.
4. HQ explicitly approves the next step.
5. A production/app promotion gate is separately defined and passed.

Any failed gate stops promotion work. This contract alone is not approval for production use.

## Explicit Non-Output Statement

This contract does not create rankings, probabilities, bands, app-readable rookie outcome columns, active model artifacts, active private scores, production formulas, Streamlit wiring, outcome-column files, or veteran outcome-head changes.
