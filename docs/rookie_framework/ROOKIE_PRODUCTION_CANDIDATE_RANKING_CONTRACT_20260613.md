# Rookie Production-Candidate Ranking Contract - 2026-06-13

## Purpose

This contract defines a rookie-only production-candidate ordering layer for v0.3. It is not production promotion. It does not replace active rankings, change private scores, modify formulas, wire app/Streamlit output, create probabilities, create bands, create outcome columns, or use veteran outcome heads.

The approved output name is:

- `rookie_production_candidate_v03`

This name means candidate/export-only. It must not be read as final rankings, probabilities, bands, outcomes, or app-ready production values.

## Inputs

The production-candidate export reads only the local Step 3 shadow ranking exports:

- `local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/rookie_shadow_ranking_v03.csv`
- `local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/rookie_shadow_ranking_premium_v03.csv`
- `local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/rookie_shadow_ranking_round2_v03.csv`
- `local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/rookie_shadow_ranking_5_04_watchlist_v03.csv`
- `local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/README_ROOKIE_SHADOW_RANKING_V03.md`

It must not read `data/`, app files, production ranking files, private-score files, formulas, outcome-column files, veteran outcome-head files, probability files, or band files.

## Outputs

The local candidate exports are written under:

`local_exports/model_v4/rookie_framework_v02/production_candidate_v03/`

Expected files:

- `rookie_production_candidate_v03.csv`
- `rookie_production_candidate_premium_v03.csv`
- `rookie_production_candidate_round2_v03.csv`
- `rookie_production_candidate_5_04_v03.csv`
- `rookie_production_candidate_manual_warnings_v03.csv`
- `rookie_production_candidate_source_safety_audit_v03.csv`
- `README_ROOKIE_PRODUCTION_CANDIDATE_V03.md`

Generated local exports must not be committed.

## Required Row Markers

Every candidate row must include:

- `production_candidate_only = yes`
- `app_read_allowed = no`
- `probabilities_created = no`

Rows missing any marker fail validation.

## Minimum Columns

The candidate CSV must include:

- `candidate_rank`
- `player_id`
- `player_name`
- `position`
- `school`
- `pick_zone`
- `tag_summary`
- `production_ready_status`
- `promotion_blockers`
- `manual_warnings`
- `source_confidence`
- `evidence_basis_summary`
- `why_ranked_here`
- `why_not_higher`
- `why_not_lower`
- `production_candidate_only`
- `app_read_allowed`
- `probabilities_created`
- `source_safety_notes`

## Production Ready Status

Allowed values:

- `ready`: no visible blockers, no manual warnings, no remaining gaps, no quarantined prohibited source terms, and source confidence is not low.
- `rankable_with_warning`: candidate can stay in the candidate order, but manual flags, soft flags, remaining gaps, low confidence, or quarantined warning terms must remain visible. This is not clean and not implementation approval.
- `manual_review_required`: candidate needs a human decision before production ranking movement. This includes unresolved premium injury review, TE exception review, or other role-defining manual questions.
- `blocked`: hard caps, source conflicts, capped/unavailable review status, or other stop conditions block production movement.
- `unavailable`: source-safe evidence is insufficient, the row needs data, or roster-declaration context is required.

`ready` does not mean app promotion is approved. It means the row has no currently visible blocker under this candidate contract.
`rankable_with_warning` does not clear warnings. It exists so a future candidate ranking can order useful players while still displaying manual review context beside every row.

## Ordering Rules

Candidate ordering is deterministic from shadow metadata only:

- shadow review group;
- production-ready status;
- source confidence;
- remaining-gap count;
- manual-flag count;
- position;
- prior shadow order;
- player name.

The candidate order may be stricter than the shadow order because blocked and unavailable rows are demoted inside their shadow group. It must not use market, rank, projection, consensus, ADP, trade value, draft-kit, legacy `private_score`, probability, or band inputs.

## 1.03 Handling

`1.03` remains empty unless a future approved source artifact opens it.

Safe candidate representation:

- no player row is created for `1.03`;
- no `1.04` row is backfilled into `1.03`;
- the README states `1.03 rows: 0`;
- future docs may represent the slot as `no_player_cleared`, `hold`, or `trade_down_review`.

## 1.04 Handling

`1.04` candidates may appear in candidate order only with warnings preserved.

The export must not auto-clear:

- injury review;
- source-limited warnings;
- route/separation/press/YAC manual flags;
- RB pass-protection/contact/fumble/first-down/goal-line gaps;
- quarantined source terms.

## Source-Safety Status Rules

Statuses that may influence candidate order:

- `use_now`: may support candidate order when provenance is preserved.
- `use_as_soft_flag`: may be bounded review context or a risk/tiebreaker, but cannot open `1.03`, override caps, or become hard private value.

Statuses that may only warn, block, or remain visible:

- `manual_review_only`: warning only; no positive private value.
- `unavailable`: remaining gap; no inference.
- `excluded`: quarantined or blocker; never positive value.
- `conflict_review`: blocker until resolved if it affects identity, role, injury, usage, or premium evidence.

## Warning Visibility Rules

Rows marked `rankable_with_warning` or `manual_review_required` must preserve:

- `promotion_blockers`
- `manual_warnings`
- `source_confidence`
- `evidence_basis_summary`
- `why_ranked_here`
- `why_not_higher`
- `why_not_lower`
- `source_safety_notes`

Warnings must not be hidden in order to make a row look clean.

## Disqualification Rules

A player is blocked from production ranking movement if any of the following are true:

- hard cap remains active;
- source conflict affects the production case;
- evidence depends on prohibited market/rank/projection material;
- missing provenance for a field that changes order;
- manual-only evidence is the sole reason for movement;
- injury risk is unresolved for a premium candidate;
- 1.03 would need to be forced open from soft evidence;
- unavailable fields would need to be inferred.

## Non-Outputs

This contract does not authorize:

- production ranking replacement;
- final rookie rankings;
- private-score changes;
- formula changes;
- app/Streamlit wiring;
- rookie probabilities;
- rookie probability bands;
- outcome-column files;
- veteran outcome heads;
- `data/` commits;
- `local_exports/` commits.

## Gate To Stage C

Stage C may audit the contract and candidate export if:

- strict review-board build passes;
- strict shadow ranking build passes;
- strict candidate build passes;
- direct harness tests pass;
- candidate rows preserve required markers;
- `1.03` remains empty;
- no production/app/private-score/probability/outcome/veteran files change.
