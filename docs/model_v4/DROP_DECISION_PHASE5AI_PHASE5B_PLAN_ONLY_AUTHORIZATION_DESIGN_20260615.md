# Drop Decision Phase 5AI Phase 5B Plan-Only Authorization Design - 2026-06-15

## Status

This document is a plan-only authorization design for Main HQ review.

Phase 5B is not opened by this document. This document does not authorize Codex to create a final or implied drop recommendation, sort or rank drop candidates, create probabilities or outcome bands, produce app-readable recommendation outputs, promote artifacts, push, deploy, or modify rookie framework files.

Current baseline:

- Branch: `work/drop-decision-day-review`
- Expected pushed checkpoint: `07a72606e404183d421ed13f76c91df919bf4234`
- Commit: `07a7260 Stabilize drop decision optional audits`
- Current allowed mode: Phase 5A human-review context only

## Exact Future Authorization Language

Main HQ must paste the following language in a later prompt before any Phase 5B decision-support work may begin:

```text
Main HQ explicitly authorizes a separate Drop Decision Phase 5B decision-support planning run only under the gates and stop rules in docs/model_v4/DROP_DECISION_PHASE5AI_PHASE5B_PLAN_ONLY_AUTHORIZATION_DESIGN_20260615.md. Phase 5B may inspect committed Phase 5A documentation and ignored local review artifacts for evidence conflicts, missing context, provenance caveats, and human-review questions. Phase 5B may not create a final or implied drop recommendation, name a final roster move, sort or rank drop candidates, create probabilities, create outcome bands, create app-readable recommendation outputs, promote artifacts, commit data/ or local_exports/, push, deploy, modify rookie framework files, use external/ranking/projection sources, or make any player-level decision output. Stop immediately if any requested output would cross those boundaries.
```

This authorization language permits only decision-support planning and evidence review. A later prompt that wants a different scope must restate the allowed outputs, forbidden outputs, gates, and stop rules in full.

## Allowed Evidence Categories

Only these evidence categories are allowed for a future Phase 5B planning run:

- committed Phase 5A and Phase 5AB documentation
- ignored local Phase 5A review artifacts under `local_exports/model_v4/`
- artifact metadata, schemas, row counts, allowed-use fields, blocked-use fields, warning flags, receipt pointers, and provenance notes
- Decision Board review context and validation-focus context
- human-review prep card context
- roster opportunity-cost context as review-only context
- external asset context as review-only context
- rookie review artifacts as separate review-only inputs
- Main HQ manually supplied notes in the later authorization prompt

The future run must treat all evidence as context for human review. It must not convert context into a final action.

## Blocked Evidence And Output Categories

The following categories remain blocked unless Main HQ creates a later, separate authorization that explicitly replaces this design:

- final or implied drop recommendations
- final cut, keep, trade, draft, or roster-move decisions
- sorted or ranked drop-candidate lists
- probabilities, win rates, odds, confidence percentages, or outcome bands
- app-readable recommendation outputs
- promoted artifacts
- production `data/` changes
- committed `local_exports/` artifacts
- external rankings, projections, ADP, trade calculators, RotoWire values, RotoWire outlooks, RotoWire rankings, RotoWire projections, or same-season final stats
- rookie framework file edits
- forcing rookie artifacts through veteran-only decision heads
- automatic roster actions

## Gates Before Any Future Phase 5B Planning Run

A future Phase 5B planning run must stop unless all gates are GREEN:

1. The current repository path is exactly the Drop Decision lane, not a rookie, outcome, production, or app lane.
2. The current branch is `work/drop-decision-day-review`.
3. Local and remote branch state are understood and reported.
4. `git status --short` is reviewed before any file write.
5. `data/` and `local_exports/` are not staged or committed.
6. Required Phase 5A review artifacts exist, are ignored, and are untracked.
7. The Decision Board remains usable only as human-review context.
8. Age-source provenance caveats are visible in the run report.
9. No requested output requires ranking, sorting, probability, band, final decision, or app-readable recommendation shape.
10. Rookie context remains separate from veteran heads and rookie framework files are not edited.

## Stop Rules

Codex must stop as RED if:

- the active path is not the Drop Decision repo
- the active branch is not `work/drop-decision-day-review`
- a Rookie WR packet or rookie-framework improvement prompt is being run instead of a Drop Decision prompt
- a prompt asks for final or implied drop guidance without a separate explicit authorization
- a requested output would sort or rank drop candidates
- a requested output would create probabilities, outcome bands, or app-readable recommendation files
- a requested action would stage, commit, or promote `data/` or `local_exports/`
- a requested action would modify rookie framework files
- a requested action would use external/ranking/projection sources
- a generated artifact or doc drift cannot be safely classified

Codex must stop as YELLOW if:

- required local review artifacts are missing but Phase 5A context is not disproven
- artifact provenance is unclear
- age coverage or review-only caveats are not visible enough for Main HQ review
- tests fail in a way that does not directly invalidate Phase 5A but requires Main HQ attention

## Required Tests And Smokes

Before any future Phase 5B planning run:

```powershell
git status --short
git diff --check
git diff --check origin/main..HEAD
python -m pytest tests/test_model_v4_phase5_clean_display_language.py
python -m pytest tests/test_navigation_compression.py
python -m pytest tests/test_model_v4_human_decision_review_prep_service.py
python -m pytest tests/test_model_v4_roster_opportunity_cost_service.py
python -m pytest tests/test_decision_board_coherence_audit.py
python -m pytest tests/test_non_formula_sanity_fixtures.py
python -m py_compile app/pages/08_june15_review.py app/navigation.py
python -m py_compile src/services/model_v4_human_decision_review_prep_service.py src/services/model_v4_roster_opportunity_cost_service.py
```

After any future Phase 5B planning document is created:

```powershell
git status --short
git diff --check
python -m pytest tests/test_model_v4_phase5_clean_display_language.py
python -m pytest tests/test_navigation_compression.py
python -m py_compile app/pages/08_june15_review.py app/navigation.py
```

Use the repository virtual environment if global `python` or `pytest` is not the configured test runtime.

## Human-Approval Boundaries

All future Phase 5B planning outputs must remain advisory and human-readable. Main HQ retains sole authority over:

- whether Phase 5B opens at all
- whether any evidence conflict is material
- whether any later recommendation-mode prompt is appropriate
- whether any roster action is taken
- whether any docs-only plan is committed
- whether any branch is pushed

Codex may prepare questions, caveat lists, metadata checks, and non-ranked review checklists only when authorized.

## Age Caveats And Missing Data Handling

The age artifact must remain local-review-only context:

- source update date: June 4, 2026
- age values are source-provided strings, not DOB-derived values
- ages must not be recalculated to today's date
- DOBs and external sources must not be used to alter the artifact
- partial coverage must be carried forward as a caveat
- missing age context must become a human-review question, not a model-side assumption

If age coverage is incomplete for a future review item, the allowed output is a neutral caveat such as `age_context_missing_or_partial`. It must not become a drop reason, rank adjustment, probability, or band.

## Rookie Context Boundary

Rookie artifacts may be inspected only as separate review-only context. A future Phase 5B planning run must not:

- edit rookie framework files
- run a Rookie WR feature-quality prompt
- force rookie rows through veteran decision heads
- turn rookie context into final draft, trade, cut, keep, or drop guidance
- use rookie ranking changes to justify a roster decision

If rookie evidence matters, the allowed output is a neutral human-review question with a receipt pointer and caveat label.

## Future Safe Output Format

A future planning run may create a docs-only, human-readable table with columns like:

| Field | Meaning |
| --- | --- |
| `review_question_id` | Stable neutral question identifier |
| `review_area` | Broad area such as roster pressure, pick context, age caveat, or external context |
| `artifact_path` | Local review artifact path or committed doc path |
| `receipt_or_schema_pointer` | Receipt, schema, or field reference |
| `evidence_conflict` | Neutral description of the conflict or missing context |
| `human_check_needed` | Question Main HQ must answer manually |
| `blocked_use` | Explicit reminder of what the row cannot be used for |
| `stop_rule_if_unresolved` | Whether unresolved context should stop a later run |

Rows must remain unordered or ordered by stable neutral identifiers only. They must not be sorted by player value, pressure, risk, rank, recommendation strength, or drop likelihood.

## Forbidden Output Format

Future outputs must not contain columns or prose equivalent to:

- `recommended_drop`
- `final_drop`
- `cut_rank`
- `drop_rank`
- `drop_score`
- `drop_probability`
- `keep_probability`
- `outcome_band`
- `recommendation_band`
- `action`
- `decision`
- `best_candidate`
- `worst_candidate`
- `top_drop_candidate`

Future outputs must also avoid narrative wording that implies one player should be dropped, kept, traded, drafted, or prioritized over another.

## Current Plan-Only Conclusion

Main HQ may review this document as a future Phase 5B authorization design packet. It is safe only as a docs-only planning artifact.

Phase 5B remains closed until Main HQ pastes a later explicit authorization prompt. This document creates no final or implied recommendation and no player-level decision output.
