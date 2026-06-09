# Veteran And Asset Research Archive

This folder archives the Deep Research reports that govern the veteran,
asset-conversion, forced-release, source-confidence, and cross-research audit
work for the LVE local-first war room.

These files are source research, not executable model output. Formula weights,
thresholds, gates, and package constants from these reports must be treated as
model-design defaults unless the later audit phase explicitly marks them as
evidence-backed.

## Archived Reports

| phase | file | status | SHA-256 |
|---|---|---|---|
| 6 | `PHASE_6_VETERAN_VALUATION.md` | complete; accepted as veteran-model foundation | `03992E6D3927D0A8C6619FFBF422D6CC641286CF57D95E4E8B2C9D3025FFA498` |
| 7 | `PHASE_7_ASSET_CONVERSION.md` | complete; accepted with coefficient caution | `6AC2827BE1310FD6CF8199CCF38EEAB05D6C07580B19DA9D6109E64DA1050BF0` |
| 8 | `PHASE_8_FORCED_RELEASE_STRATEGY.md` | complete; strategy math must stay scenario-aware | `7DDDC44741587C81F01D0F19825C1691FF9BE6AB4D1171D7C640C526AA4C1F75` |
| 9 | `PHASE_9_SOURCE_CONFIDENCE_OVERRIDES.md` | complete; accepted for source and override policy | `AF8A6F906700FD011EF9A32D8FCDAFB327671A0377593B6F4957CC59BE7C3747` |
| 10 | `PHASE_10_CROSS_RESEARCH_AUDIT.md` | complete; controlling audit for implementation caution | `EA4670672884053751DF2D6ABC7811B714E8F7CF16CF3C9E12E684B6FF7E443A` |
| 11 | `PHASE_11_PUBLIC_SOURCE_DATA_PLAN.md` | complete; accepted as v1 public-source import policy | `30195E036F8223636A735FCD67FA7A84D16A6FD67BA98BCC7B09FE0B30F2F13E` |

## Audit Outputs

| file | purpose |
|---|---|
| `RESEARCH_AUDIT_TABLE.md` | Human-readable implementation disposition table for Phase 6-10 claims. |
| `research_audit_table.csv` | CSV version of the audit table for future app/fixture ingestion. |

## Implementation Locks

| phase | output | status |
|---|---|---|
| B1 | `sample_data/veteran_model_v1/veteran_feature_registry.csv` | Expanded veteran registry with Phase 6/10 feature metadata and `active_v1` / `future_candidate` / `display_only` / `rejected` scoring status. |
| Stage 2 | `src/services/public_source_import_service.py` | V1 source policy lock for approved, limited, optional paid, rejected, and unknown public-source imports. |
| Stage 3 | `templates/real_data_inputs/public_sources/` | Phase 11 public-source CSV schemas for source catalog, projections, market, role, injury, bio, and normalized veteran feature backfill. |
| Stage 5 | `local_exports/public_source_snapshots/` | Ignored local source snapshots with manifest, row counts, validation status, and file checksums. |
| Stage 6 | `src/services/public_source_import_service.py` | Review-safe public-source player matching by player key, platform IDs, and unambiguous normalized name fallback. |
| Stage 7 | `src/services/public_source_import_service.py` | Review-only feature-normalization readiness that maps matched source domains and normalized backfill rows to active veteran features. |
| Stage 8 | `local_exports/public_source_normalization_worklists/` | Ignored normalization worklist exports for unresolved active veteran features. |
| Stage 9 | `app/pages/07_source_overrides.py` | Review-only backfill acceptance gate for normalized veteran feature inputs. |
| Stage 10 | `local_exports/public_source_model_input_candidates/` | Ignored accepted-backfill exports in veteran feature-score candidate shape. |
| Stage 11 | `app/pages/07_source_overrides.py` | Review-only validation gate for candidate veteran feature-score rows. |
| Stage 12 | `app/pages/07_source_overrides.py` | Review-only candidate coverage gate for later isolated model previews. |
| Stage 13 | `local_exports/public_source_model_previews/` | Ignored isolated veteran-model preview exports for complete accepted candidate rows. |
| Stage 14 | `app/pages/07_source_overrides.py` | Review-only gate for isolated preview outputs before any future promotion workflow. |
| Stage 15 | `app/pages/07_source_overrides.py` | Read-only comparison of review-gated preview outputs against the selected pack's live model outputs. |
| Stage 16 | `local_exports/public_source_model_promotion_candidates/` | Ignored promotion-candidate exports for ready preview-vs-live rows only. |
| Stage 17 | `app/pages/07_source_overrides.py` | Review-only admission gate for promotion candidates against the currently selected pack. |
| Stage 18 | `local_exports/data_packs/` | Explicit apply workflow that writes a new generated data-pack copy from ready promotion candidates. |
| Stage 19 | `app/pages/07_source_overrides.py` | Review-only admission gate for generated applied data-pack copies. |
| Stage 20 | `app/components/data_pack_selector.py` | Data-pack catalog and selector surface generated applied-pack admission status. |
| Stage 21 | `app/components/data_pack_selector.py` | Sidebar notice explains the selected generated applied pack's admission reason and next action. |
| Stage 22 | `src/services/data_pack_admission_service.py` | Import Review admission decision honors generated applied-pack manifests. |
| Stage 23 | `src/services/draft_freeze_service.py` | Draft Freeze requires formal admission readiness for final draft-day freezes. |
| Stage 24 | `src/services/draft_freeze_service.py` | Draft-day README labels final boards versus review snapshots. |
| Stage 25 | `src/services/draft_freeze_service.py` | Freeze exports a one-row money-decision certificate. |

B1 intentionally keeps current veteran scoring behavior limited to `active_v1`
features. Research-backed future features are now tracked in the registry, but
they cannot change scores until a later scoring phase promotes them.

Stage 2 does not score players. It only blocks rejected machine-ingested sources,
warns on unknown source references, and displays the allowed/forbidden use policy
in Sources & Overrides.

Stage 3 also does not score players. It upgrades the import templates and
validators so future source snapshots can be staged in the full Phase 11 shape
before any raw row is normalized into model features.

Stage 5 also does not score players. It freezes raw source CSVs for
reproducibility before normalization or scoring and refuses to snapshot blocked
source inputs.

Stage 6 also does not score players. It identifies matched, ambiguous, and
unmatched source rows so normalization can stop before bad identity merges.

Stage 7 also does not score players. It shows whether each active veteran
feature is already normalized, has matched raw source evidence ready for
normalization, needs a manual/local baseline, or is still missing source data.

Stage 8 also does not score players. It writes a CSV worklist of unresolved
feature-normalization tasks so the next data-prep pass can fill real 0-100
feature scores with provenance.

Stage 9 also does not score players. It labels normalized backfill rows as
accepted, review, or blocked before any later model-run input step can consume
them.

Stage 10 also does not score players. It exports accepted normalized backfill
rows in `veteran_feature_scores.csv` shape for review by a later model-run input
step, but it does not overwrite committed model inputs or generate recommendations.

Stage 11 also does not score players. It validates candidate feature-score rows
for player identity, position agreement, active feature keys, duplicate
player-feature rows, normalized score bounds, and safe missing/override flags.

Stage 12 also does not score players. It groups validated candidate rows by
rostered player and active V1 feature requirements so incomplete players are
identified before any later isolated model preview.

Stage 13 scores preview-only outputs, but it does not change live decisions. It
builds a self-contained veteran-model input folder from complete-coverage
players and accepted candidate rows, runs the veteran scorer there, and writes
preview outputs under ignored `local_exports/public_source_model_previews/`.
The selected data pack, committed model inputs, and app recommendations are not
overwritten.

Stage 14 also does not change live decisions. It reads isolated preview outputs
and classifies each row as `ready`, `review`, or `blocked` based on warning
status, confidence, missing-data penalties, risk level, and schema warnings.
`ready` means safe to compare against live outputs; it is not automatic
permission to publish or promote scores.

Stage 15 also does not change live decisions. It compares review-gated preview
rows against the selected pack's current `model_outputs.csv` and flags material
keeper/drop movement, missing live baselines, or blocked preview rows before any
future promotion workflow can exist.

Stage 16 also does not change live decisions. It exports only `ready`
preview-vs-live rows into an ignored `model_outputs`-shaped promotion candidate
CSV with a manifest. This is a package for final human review, not a write into
the selected pack.

Stage 17 also does not change live decisions. It revalidates promotion candidates
against the currently selected pack so stale exports, missing live baselines,
missing preview provenance, or material score movement are caught before any
future explicit apply workflow.

Stage 18 is the first apply workflow, but it still never mutates the selected
pack in place. It copies the selected data pack into `local_exports/data_packs/`,
replaces only `model_outputs.csv` rows for `ready` promotion candidates, and
writes an apply manifest so the generated pack can be selected and reviewed.

Stage 19 does not change live decisions. It validates generated applied packs
after creation and classifies each pack as `ready`, `review`, or `blocked`.
`ready` means the generated pack can be selected for final app review; it does
not automatically make that pack the active draft-day truth.

Stage 20 also does not change live decisions. It carries the Stage 19 generated
pack admission status into the data-pack catalog and sidebar selector so an
applied pack cannot look like an ordinary generated folder without its
`ready`/`review`/`blocked` label.

Stage 21 also does not change live decisions. It adds a selected-pack sidebar
notice for generated applied packs so the admission reason and next action are
visible at the moment of selection.

Stage 22 makes the formal Import Review admission decision aware of generated
applied-pack manifests. A generated pack with zero applied rows, missing usable
model outputs, or validation errors is blocked; a generated pack with remaining
health review issues stays in review.

Stage 23 makes Draft Freeze use the same admission decision. Final draft-day
freezes require admission `ready`; non-ready packs can only be frozen as explicit
review snapshots, and the freeze metadata records that distinction.

Stage 24 makes that distinction visible in the human draft-day README. Final
freezes are labeled `FINAL DECISION BOARD`; review snapshots are labeled
`REVIEW SNAPSHOT - NOT A FINAL BOARD` with the admission decision and use policy.

Stage 25 adds a machine-readable `money_decision_certificate.csv` to each freeze.
It records whether the artifact is a final board or review-only, whether it can
be used for money decisions, and the next action.

## Implementation Rules From The Archive

- League rank is forced-release exposure only, never player quality.
- Public market value is liquidity context, not private LVE value.
- Projections, role, usage, and source provenance outrank generic rankings.
- QB and TE suppression should be soft and replacement-aware, with elite escape hatches.
- First-down scoring should be a modest LVE overlay unless already embedded in projections.
- Future-pick discounts, package penalties, owner-behavior scores, and reacquisition probabilities are calibration-required heuristics.
- Manual overrides may alter inputs or provenance only; final score overrides are rejected.
- V1 public-source imports should use Sleeper, Fantasy Football Analytics,
  DynastyProcess, and nflverse as the free/public backbone.
- KeepTradeCut scraping, raw FantasyPros page scraping, and FantasyCalc as a
  required automated dependency are rejected for v1.
- League-rank PDF data remains forced-release exposure only, never player value.

## Next Phase

Phase B1 expanded the veteran registry. The next scoring phases should promote
future-candidate features only when formula weights, provenance labels, tests,
and calibration notes are updated together.
