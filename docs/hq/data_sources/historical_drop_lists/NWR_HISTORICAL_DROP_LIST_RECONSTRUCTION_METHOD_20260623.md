# NWR Historical Drop List Reconstruction Method - 20260623

## Purpose

This folder fills the historical dropped-veteran gap with clearly labeled evidence rows and synthetic proxy rows. It is intended for model accountability, backtesting shape, sensitivity testing, stress testing, simulation/backtest robustness checks, and gap analysis. It is not an approval to change rankings, app logic, Outcome logic, Drop Decision logic, latest pointers, pinned snapshots, or frozen draft-day artifacts.

## Outputs

- `NWR_HISTORICAL_DROP_LIST_RECONSTRUCTION_2010_2026.csv`: combined actual, inferred, and proxy rows.
- `NWR_RECENT_ACTUAL_OR_INFERRED_DROP_LISTS_2021_2026.csv`: recent evidence-backed rows only. No 2021 actual or inferred evidence was found in this pass, so 2021 appears only in the proxy file and combined file.
- `NWR_PROXY_DROP_LISTS_2010_2021.csv`: synthetic proxy rows only.

## Usage Rule

Rows with `source_class = PROXY_DROP`, `confidence = PROXY_ONLY`, or `confidence = LOW` may be used only for sensitivity testing, stress testing, simulation/backtest robustness checks, and gap analysis.

They may not be used as direct training truth, rank penalties, proof a player was a bad cut, evidence that a player was actually dropped, source-truth labels, private value, hidden sort, or draft advice.

`ACTUAL_DROP` and high-confidence `INFERRED_DROP` rows may be analyzed separately from proxy rows. Inferred rows still require caution and should not be over-weighted unless later transaction/commissioner evidence upgrades them.

## What Was Actual

Actual rows are rows with an explicit dropped/cut source:

- 2026: 12 rows from the approved Drop Decision lane-exchange package `drop_decision/dropped_veterans`, snapshot `20260620_131511_identity_normalized_live_test`. The package is approved only for first local live-test validation and mock-draft read-only validation. It is not final draft-day approval and not production data approval. Interpret these as draft availability/unprotected context, not as proof that any player was a bad cut.
- 2025: 10 rows from `LVE rosters 2025 Cut List.pdf`, where the extracted PDF text contains explicit `CUT` labels.

## What Was Inferred

Inferred rows are near-actual cut-list rows from explicit LVE cut-list PDFs where the text extraction showed top-5/unprotected blocks rather than transaction-confirmed drops:

- 2024: `LVE Cut List 2024.pdf`
- 2023: `LVE Cut List 2023.pdf`
- 2022: `LVE rosters RDD 081822 for draft.pdf`

These rows are labeled `INFERRED_DROP` with `MEDIUM` confidence. They should be treated as reviewed cut-list/unprotected evidence, not as Sleeper transaction truth.

## What Was Synthetic/Proxy

The 2010-2021 rows are `PROXY_DROP` and `PROXY_ONLY`. They were generated from an era-plausible roster-bubble universe of older veterans, fringe quarterbacks, low-scarcity tight ends, kickers, and defenses. They are not historical LVE cuts. No 2021 league cut/drop evidence was found, so every 2021 row is proxy-only.

## Status Summary

- 2010-2021 are proxy-only.
- 2022-2024 are inferred/unprotected PDF rows unless upgraded by later evidence.
- 2025 follows explicit PDF `CUT` evidence from the available cut-list PDF.
- 2026 has actual/current availability evidence from the approved Drop Decision package, but should be interpreted as draft availability/unprotected context, not necessarily bad cuts.
- No 2021 actual evidence exists in this reconstruction.

## Season Coverage

| Season | ACTUAL_DROP | INFERRED_DROP | PROXY_DROP |
| --- | ---: | ---: | ---: |
| 2010 | 0 | 0 | 40 |
| 2011 | 0 | 0 | 40 |
| 2012 | 0 | 0 | 40 |
| 2013 | 0 | 0 | 40 |
| 2014 | 0 | 0 | 40 |
| 2015 | 0 | 0 | 40 |
| 2016 | 0 | 0 | 40 |
| 2017 | 0 | 0 | 40 |
| 2018 | 0 | 0 | 40 |
| 2019 | 0 | 0 | 40 |
| 2020 | 0 | 0 | 40 |
| 2021 | 0 | 0 | 40 |
| 2022 | 0 | 50 | 0 |
| 2023 | 0 | 50 | 0 |
| 2024 | 0 | 49 | 0 |
| 2025 | 10 | 0 | 0 |
| 2026 | 12 | 0 | 0 |

## Proxy Cut Score

`proxy_cut_score` is a deterministic stress-test score, not a model score. It combines:

- age/decline pressure by position,
- roster scarcity by position in a 10-team 1QB keeper format,
- synthetic prior-year production and position rank,
- extra replaceability pressure for kickers and defenses,
- extra penalty for fringe or backup quarterbacks in 1QB.

The score exists only to sort proxy stress-test rows by cut plausibility. It must not be used as private value, draft advice, hidden sort, direct training truth, rank penalty, proof of a bad cut, actual-drop evidence, source-truth label, or historical truth.

## Caveats

- 2026 rows depend on the approved local-live-test Drop Decision package. The package itself says final draft-day approval remains separate.
- 2025 rows are explicit PDF `CUT` rows, but this pass did not re-match every row to Sleeper transactions.
- 2022-2024 rows come from extracted PDF top-5/unprotected blocks and are intentionally classified as inferred.
- No 2021 cut-list document or transaction evidence was found; 2021 is synthetic proxy-only.
- 2010-2021 rows are proxy-only and can be wrong about real LVE roster history by design.
- `player_id` is blank for recent PDF/package evidence unless a safe source ID was directly available. Proxy rows use local synthetic IDs prefixed with `proxy_`.
- Market value is intentionally blank throughout this reconstruction.

## Recommended Next Step For True History

Recover true historical cut lists by locating old commissioner emails/docs, Sleeper historical league chains with valid `previous_league_id`, archived draft rooms, roster export PDFs, and transaction logs. When transaction evidence exists, promote rows from `INFERRED_DROP` or `PROXY_DROP` only after a separate human review.

## Guardrail Notes

This pass created documentation/data-source files only under `docs/hq/data_sources/historical_drop_lists` and updated personal accountability docs. It did not mutate shared raw data, latest pointers, pinned snapshots, frozen board files, app code, model logic, or ranking logic.

## Build Summary

- Built at: 2026-06-24T02:22:37.167801+00:00
- Combined rows: 651
- ACTUAL_DROP rows: 22
- INFERRED_DROP rows: 149
- PROXY_DROP rows: 480
