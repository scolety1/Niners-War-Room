# Named Player Ranking Audit

Date: 2026-05-12

Active pack: `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`

Audit artifacts:

- `local_exports/named_player_ranking_receipt_audit.csv`
- `local_exports/named_player_pair_audit.csv`
- `local_exports/named_player_pair_receipts.csv`

## Scope

This pass audits the named players the user called out: Luther Burden, Brian Thomas, De'Von Achane, Lamar Jackson, Kaleb Johnson, Jayden Higgins, Chase Brown, Bijan Robinson, Jahmyr Gibbs, Kyren Williams, Jaxon Smith-Njigba, and Tee Higgins.

The audit compares lifecycle assignment, source coverage, Model Value, Keep Priority, Cut Risk, visible score source, identity matching, and top receipt drivers. No formula weights were changed.

## Supported Patches

The Named Player Audit now reads the active War Board rows instead of raw `model_outputs.csv`. This prevents an audit page from silently inspecting a stale data-pack score while the visible app is using active stats-first preview rows.

The audit receipt matcher now joins selected players by normalized player name plus position when the visible War Board row uses a Sleeper ID and the receipt row uses a GSIS/nflverse ID. This fixed missing receipt context for active stats-first rows.

Source coverage now treats stale stats-first production as review coverage. For a 2026 decision pack, production sourced only through 2024 is not enough to treat current veteran/young-player rankings as clean.

## Major Finding

The active public nflverse import currently appears to stop at 2024 player stats. The active pack is a 2026 pre-declaration pack, so the model needs 2025 production and role/usage data before these rankings can be trusted for money decisions.

This is especially important for players whose 2025 season would materially change the receipt:

- Jaxon Smith-Njigba versus Tee Higgins
- Brian Thomas versus other young WRs
- RB ordering among Bijan Robinson, Jahmyr Gibbs, Kyren Williams, De'Von Achane, and Chase Brown
- young bridge players such as Luther Burden, Kaleb Johnson, and Jayden Higgins

## Named Pair Read

| pair | current leader | audit read |
|---|---|---|
| Brian Thomas vs Luther Burden | Brian Thomas | Direction is plausible because Brian Thomas has stronger visible NFL evidence, but both remain review-only until 2025/role coverage is refreshed. |
| Luther Burden vs Chase Brown | Chase Brown | This is not final truth. Luther is a low-confidence young bridge row and Chase has more NFL evidence in the current imported data. |
| Kaleb Johnson vs Kyren Williams | Kyren Williams | Supported by current receipts because Kyren has NFL production and Kaleb is low-confidence bridge/prospect evidence. Still review-only. |
| JSN vs Tee Higgins | Tee Higgins | Treat as source-blocked, not a settled model opinion. JSN is likely missing the season that matters most for this comparison. |
| Kyren vs Bijan | Bijan | Supported directionally by young elite RB value plus bridge context. Needs fresh 2025 production/role data before final use. |
| Kyren vs Gibbs | Gibbs | Supported directionally, but still source-review because production and role coverage are stale/proxy-level. |
| Kyren vs Jeanty | Kyren | Expected with Jeanty as a low-confidence young/incoming asset in the current preview. Draft-specific rookie board should handle incoming rookies separately. |

## Why Some Rankings Look Wrong

The receipts are doing their job by exposing that several rankings are driven by incomplete or stale source inputs. A surprising rank is not automatically a formula bug. In this pass, the strongest concrete blocker is data freshness: the active stats import needs the most recent completed NFL season and stronger role/usage coverage.

For JSN specifically, the current imported features make his production, efficiency, and first-down/TD fit look lower than Tee Higgins. That should not be accepted as a final model conclusion until 2025 stats and role data are imported and the stats-first preview is regenerated.

## Decision Status

Rankings should remain review-only.

Before roster decisions become decision-ready, the next model-data action is:

1. Import/derive 2025 player production, first-down, and role/usage data.
2. Regenerate normalized stats-first features.
3. Regenerate preview outputs and receipts.
4. Re-run the named-player audit and pair fixtures.
5. Only then inspect whether remaining weird ranks are formula issues or real model disagreement.
