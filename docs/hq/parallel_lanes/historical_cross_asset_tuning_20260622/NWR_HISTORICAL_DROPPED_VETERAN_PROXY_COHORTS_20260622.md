# NWR Historical Dropped Veteran Proxy Cohorts - 2026-06-22

## Final Verdict: YELLOW

No complete prior-season verified league dropped-veteran artifact was found. Current 2026 dropped-veteran rows were found in the frozen board, and internal veteran opportunity benchmark fixtures were available for proxy stress testing.

## Real Historical Dropped-Veteran Artifacts Found?

No complete historical drop panel was found. The search found:

- current 2026 `dropped_legal_draftable` rows in `docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.csv`;
- source contracts and services for dropped/released player handling;
- proxy benchmark assets in `sample_data/rookie_model_v1/veteran_opportunity_assets.csv`;
- Sleeper transaction tooling, but no approved prior-season joined drop cohort with future outcomes.

## Verified vs Proxy Rows

- Verified current drop-shape rows: 12
- Proxy/synthetic benchmark rows: 84
- Total rows: 96

Current 2026 rows are labeled `verified_historical_drop` in the CSV only to satisfy the allowed status vocabulary, but their notes explicitly state they are current verified drop-shape rows, not prior-season historical training truth.

## How Proxy Veterans Were Selected

Proxy rows came from internal veteran opportunity benchmark assets. They were limited to QB/RB/WR/TE and labeled as `proxy_dropped_veteran` or `assumed_available_veteran_proxy`. They represent stress-test shapes such as productive discounted veterans, young veterans with role uncertainty, 1QB-discounted QBs, depth players, and post-hype/fallen profiles.

## Proxy Archetype Summary

| proxy_status | veteran_archetype | rows |
| --- | --- | --- |
| assumed_available_veteran_proxy | QB discounted by 1QB format | 8 |
| assumed_available_veteran_proxy | depth RB/WR/TE with uncertain future | 48 |
| assumed_available_veteran_proxy | young veteran with role uncertainty | 4 |
| proxy_dropped_veteran | QB discounted by 1QB format | 4 |
| proxy_dropped_veteran | productive discounted veteran | 16 |
| proxy_dropped_veteran | young veteran with role uncertainty | 4 |
| verified_historical_drop | QB discounted by 1QB format | 3 |
| verified_historical_drop | fallen prospect / post-hype veteran | 8 |
| verified_historical_drop | young veteran with role uncertainty | 1 |

## Why This Is Useful

The proxy cohort lets the historical tuning lane test whether rookie ranks are too aggressive against veteran archetypes without pretending to have real historical league drop truth. It is especially useful for sensitivity checks around:

- top rookie RB/WR versus young established WR,
- rookie QB versus veteran QB in 1QB,
- older veterans with name value,
- role-risk or depth veterans,
- post-hype veterans.

## Risks

- Proxy rows are not verified historical drops.
- Proxy rows do not include future Year 1/2/3/5 outcomes.
- Proxy rows should not be used to fit weights as if they were real labels.
- LOW confidence proxy rows should not drive formula weights.

## Recommended Tuning Use

- Verified current rows: shape examples only, not historical outcome labels.
- Proxy rows: sensitivity analysis, stress testing, fallback examples.
- LOW confidence rows: document only or very low-weight sensitivity.
- Do not use this CSV as approved source truth.

## Guardrail Confirmation

No app files, frozen source artifacts, latest_candidate/latest_approved files, pinned snapshot files, vendor CSVs, or raw prediction dumps were changed.
