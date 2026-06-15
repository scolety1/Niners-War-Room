# Rookie Research-to-Analyzer Reconciliation Audit

Date: 2026-06-15

Lane: Rookie Codex lane only

Verdict: YELLOW

## Executive Verdict

The rookie research process is partially feeding the analyzer correctly, but the current top-10 advisory table is not trustworthy as a complete draft board yet.

The analyzer is source-safe and warning-visible for the players that successfully reached structured analyzer fields. The priority premium cluster is present, ordered, and protected by visible warnings or manual-review gates. However, several important names are present somewhere in source-safe local exports but remain `unavailable` because low source confidence, missing structured fields, or gate semantics prevent them from entering the usable advisory tier.

This is not a production failure, because no production ranking, private score overwrite, probability, band, app wiring, or veteran outcome head was created. It is a reconciliation warning: Tim can manually use the analyzer as a warning-visible advisory board for included players, but should not treat the top table as exhaustive.

## Files Inspected

- `docs/rookie_framework/*.md`
- `scripts/rookie_framework/build_rookie_review_board_v03.py`
- `scripts/rookie_framework/build_rookie_shadow_ranking_v03.py`
- `scripts/rookie_framework/build_rookie_production_candidate_v03.py`
- `scripts/rookie_framework/build_rookie_analyzer_v03.py`
- `scripts/rookie_framework/build_rookie_draft_day_simulation_v03.py`
- `tests/test_rookie_review_board_v03.py`
- `tests/test_rookie_shadow_ranking_v03.py`
- `tests/test_rookie_production_candidate_v03.py`
- `tests/test_rookie_analyzer_v03.py`
- `tests/test_rookie_draft_day_simulation_v03.py`
- `local_exports/model_v4/rookie_framework_v02/review_board_v03/rookie_review_board_v03.csv`
- `local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/rookie_shadow_ranking_v03.csv`
- `local_exports/model_v4/rookie_framework_v02/production_candidate_v03/rookie_production_candidate_v03.csv`
- `local_exports/model_v4/rookie_framework_v02/rookie_analyzer_v03/rookie_analyzer_v03.csv`
- `local_exports/model_v4/rookie_framework_v02/draft_day_simulation_v03/rookie_draft_day_simulation_v03.csv`
- Source-safe local export folders under `local_exports/model_v4/rookie_framework_v02/`, including CFBD, RotoWire, charting-gap, deep-research, normalization, applied-framework, triage, and v0.3 candidate/audit exports.

## Commands Run

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git log --oneline -8
Get-ChildItem -Path local_exports/model_v4/rookie_framework_v02 -Directory
Get-ChildItem -Path scripts/rookie_framework -File
Get-ChildItem -Path tests -File
python scripts/rookie_framework/build_rookie_review_board_v03.py --strict
python scripts/rookie_framework/build_rookie_shadow_ranking_v03.py --strict
python scripts/rookie_framework/build_rookie_production_candidate_v03.py --strict
python scripts/rookie_framework/build_rookie_analyzer_v03.py --strict
python scripts/rookie_framework/build_rookie_draft_day_simulation_v03.py --strict
python tests/test_rookie_review_board_v03.py
python tests/test_rookie_shadow_ranking_v03.py
python tests/test_rookie_production_candidate_v03.py
python tests/test_rookie_analyzer_v03.py
python tests/test_rookie_draft_day_simulation_v03.py
python -m pytest tests/test_rookie_review_board_v03.py tests/test_rookie_shadow_ranking_v03.py tests/test_rookie_production_candidate_v03.py tests/test_rookie_analyzer_v03.py tests/test_rookie_draft_day_simulation_v03.py -q
```

Pytest result: unavailable. `python -m pytest ...` failed with `No module named pytest`. No package was installed.

## Build and Harness Results

- Review-board strict build: PASS
- Shadow-ranking strict build: PASS
- Production-candidate strict build: PASS
- Analyzer strict build: PASS
- Draft-day simulation strict build: PASS
- Direct review-board harness: PASS
- Direct shadow-ranking harness: PASS
- Direct production-candidate harness: PASS
- Direct analyzer harness: PASS
- Direct draft-day simulation harness: PASS

Current analyzer counts from strict build:

- `ready`: 0
- `rankable_with_warning`: 42
- `manual_review_required`: 7
- `blocked`: 43
- `unavailable`: 119
- total analyzer rows: 211

## Reconciliation Export

Created local-only export:

`local_exports/rookie_framework/research_to_analyzer_reconciliation_20260615/rookie_research_to_analyzer_reconciliation_20260615.csv`

The export reconciles 27 requested players across research docs, source-safe local exports, review board, shadow ranking, production candidate, analyzer output, and draft-day simulation.

Requested-player reconciliation counts:

- `rankable_with_warning`: 12
- `manual_review_required`: 3
- `unavailable`: 8
- `blocked`: 4

Issue classification counts:

- `research_flowed_warning_visible`: 12
- `manual_or_injury_gate`: 3
- `structured_field_or_gate_gap`: 8
- `correct_qb_exception_block_for_1qb`: 4

## Player-by-Player Reconciliation

| Player | Analyzer Name | Pos | Rank | Status | Research Docs | Source Exports | Reconciliation |
|---|---:|---:|---:|---|---|---|---|
| Jeremiyah Love | Jeremiyah Love | RB | 1 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| Denzel Boston | Denzel Boston | WR | 2 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| KC Concepcion | KC Concepcion | WR | 3 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| Makai Lemon | Makai Lemon | WR | 4 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| Chris Bell | Chris Bell | WR | 5 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| Germie Bernard | Germie Bernard | WR | 6 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| Zachariah Branch | Zachariah Branch | WR | 7 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| Kaelon Black | Kaelon Black | RB | 8 | manual_review_required | yes | yes | Manual/injury gate remains active. |
| Jordyn Tyson | Jordyn Tyson | WR | 9 | manual_review_required | yes | yes | Manual/injury gate remains active. |
| J'Mari Taylor | J'Mari Taylor | RB | 10 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| Carnell Tate | Carnell Tate | WR | 86 | unavailable | no | yes | Source-safe evidence exists, but analyzer gate leaves him unavailable. |
| Nicholas Singleton | Nicholas Singleton | RB | 51 | unavailable | yes | yes | Research exists, but structured RB fields/gates leave him unavailable. |
| Barion Brown | Barion Brown | WR | 82 | unavailable | no | yes | Source-safe evidence exists, but analyzer gate leaves him unavailable. |
| Max Klare | Max Klare | TE | 136 | unavailable | no | yes | Source-safe evidence exists, but TE gate leaves him unavailable. |
| Jack Velling | Jack Velling | TE | 150 | unavailable | no | yes | Held until roster declaration plus low source confidence. |
| Jadarian Price | Jadarian Price | RB | 62 | unavailable | no | yes | Source-safe evidence exists, but RB gate leaves him unavailable. |
| Kenyon Sadiq | Kenyon Sadiq | TE | 134 | unavailable | no | yes | Source-safe evidence exists, but TE gate leaves him unavailable. |
| Eli Stowers | Eli Stowers | TE | 48 | manual_review_required | yes | yes | TE exception/manual-review gate remains active. |
| Omar Cooper Jr. | Omar Cooper | WR | 42 | rankable_with_warning | no | yes | Alias maps to Omar Cooper; warning-visible flow works. |
| Antonio Williams | Antonio Williams | WR | 80 | unavailable | no | yes | Source-safe evidence exists, but analyzer gate leaves him unavailable. |
| Jonah Coleman | Jonah Coleman | RB | 19 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| Kaytron Allen | Kaytron Allen | RB | 16 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| Emmett Johnson | Emmett Johnson | RB | 12 | rankable_with_warning | yes | yes | Research flowed; warnings visible. |
| Drew Allar | Drew Allar | QB | 192 | blocked | yes | yes | Correctly blocked by 1QB/QB exception logic. |
| Cade Klubnik | Cade Klubnik | QB | 193 | blocked | yes | yes | Correctly blocked by 1QB/QB exception logic. |
| Garrett Nussmeier | Garrett Nussmeier | QB | 183 | blocked | no | yes | Correctly blocked by 1QB/QB exception logic. |
| Carson Beck | Carson Beck | QB | 178 | blocked | no | yes | Correctly blocked by 1QB/QB exception logic. |

## Top Reconciliation Failures

1. Carnell Tate is present in source-safe local exports but unavailable at analyzer rank 86 due to low source confidence. This needs source refresh or field mapping repair before draft use.
2. Nicholas Singleton is present in research docs and exports but unavailable at analyzer rank 51 due to low source confidence and many missing RB structured fields. This looks like a structured-field/gate gap, not a pure absence of evidence.
3. Barion Brown is present in source-safe local exports but unavailable at analyzer rank 82 due to low source confidence. WR evidence needs normalization into usable fields.
4. Antonio Williams is present in source-safe local exports but unavailable at analyzer rank 80 due to low source confidence. WR role/path evidence needs review.
5. Jadarian Price is present in source-safe local exports but unavailable at analyzer rank 62 due to low source confidence. RB role/first-down/contact fields need refresh.
6. Kenyon Sadiq is present in source-safe local exports but unavailable at analyzer rank 134 due to low source confidence. TE exception criteria need source refresh or gate review.
7. Max Klare is present in source-safe local exports but unavailable at analyzer rank 136 due to low source confidence. TE usage and role-path fields are not strong enough.
8. Jack Velling is present in source-safe local exports but unavailable at analyzer rank 150 due to `hold_until_roster_declaration` and low source confidence. This is a valid gate, but it keeps him out of live draft usefulness.
9. Eli Stowers is present but `manual_review_required`; TE exception evidence is not ready enough for direct use.
10. Omar Cooper Jr. maps to Omar Cooper and is warning-rankable, but the alias should be made explicit in future docs/exports to avoid Tim thinking he is missing.

## Evidence Flow Findings

The premium cluster is flowing correctly from research into analyzer fields:

- Jeremiyah Love
- Denzel Boston
- KC Concepcion
- Makai Lemon
- Chris Bell
- Germie Bernard
- Zachariah Branch
- J'Mari Taylor
- Jonah Coleman
- Kaytron Allen
- Emmett Johnson

The warning fields remain visible for:

- route/separation/press/YAC manual review
- first-down and short-yardage gaps
- RB contact/pass-pro/fumble gaps
- injury flags
- source-limited profiles
- quarantined public ranking, projection, and ADP terms

The unavailable group is the main problem. Several players are present in source-safe local exports but do not appear as usable advisory candidates because the analyzer still treats low source confidence or missing structured fields as unavailable rather than warning-rankable.

## League-Fit Findings

The analyzer remains aligned with Tim's 10-team, 1QB, non-PPR, first-down-sensitive format in these ways:

- Rookie QBs are not elevated just because of name value or draft interest.
- Non-rushing QBs remain blocked in 1QB unless a separate exception is approved.
- RBs and WRs carry first-down, route, contact, and role-path warnings.
- TE exceptions remain manual-review gated instead of being forced into the board.

The main format concern is completeness, not contamination. Some RB/WR/TE names that could matter for a manual draft board are currently unavailable because the source-safe evidence is not normalized strongly enough.

## Source-Safety Findings

No evidence was found that ADP, public rankings, consensus, projections, trade calculators, or market values are being used as private value inputs in the analyzer. These terms appear as quarantined warning context only.

No private score overwrite was found.

No rookie probabilities or bands were created.

No production ranking promotion was found.

No app/Streamlit wiring was changed.

No Outcome HQ files, outcome probability work, outcome columns, or veteran outcome heads were touched.

## Is The Current Top-10 Advisory Table Trustworthy?

Partially.

It is trustworthy as a source-safe, warning-visible advisory table for players that successfully reached structured analyzer fields. It is not trustworthy as a complete top-10 rookie draft board because several important names are unavailable despite appearing in source-safe local exports.

Tim can safely use it for manual review only if he treats the top table as a candidate board, not a final ranking, and checks the unavailable/manual-review reconciliation list before passing on any notable player.

## How Tim Can Safely Use This In Draft

- Use `rankable_with_warning` players only with warnings visible.
- Do not treat any player as clean `ready`; current `ready` count is 0.
- Treat 1.03 as trade-down/manual-review unless Tim separately clears a player.
- Treat Kaelon Black, Jordyn Tyson, and Eli Stowers as manual decisions, not ranking answers.
- Before skipping Carnell Tate, Nicholas Singleton, Barion Brown, Antonio Williams, Jadarian Price, Kenyon Sadiq, Max Klare, or Jack Velling, run a source refresh or gate/mapping repair pass.
- Keep QBs blocked unless Tim explicitly wants a separate 1QB exception review.

## Do Not Use For Production Yet

Do not use this analyzer output for:

- production rankings
- private-score replacement
- probabilities
- probability bands
- app or Streamlit display
- outcome columns
- veteran outcome heads
- public rank/ADP/projection/market-influenced scoring

## Next Best Prompt

Run a rookie-only analyzer evidence refresh and gate/mapping repair plan for the unavailable-but-source-present players:

- Carnell Tate
- Nicholas Singleton
- Barion Brown
- Antonio Williams
- Jadarian Price
- Kenyon Sadiq
- Max Klare
- Jack Velling

The next pass should not change scoring logic first. It should inspect whether source-safe evidence already exists but is missing normalized structured fields, then propose the smallest safe patch to make valid evidence visible as warnings instead of silently burying players as unavailable.
