# Rookie Framework v0.3 Step 2 Review Board README

## What Step 2 Created

Step 2 adds a deterministic rookie-only review-board exporter:

- `scripts/rookie_framework/build_rookie_review_board_v03.py`
- `tests/test_rookie_review_board_v03.py`
- `docs/rookie_framework/ROOKIE_REVIEW_BOARD_EXPORT_20260613.md`
- `docs/rookie_framework/README_ROOKIE_FRAMEWORK_V03_STEP2_REVIEW_BOARD.md`

The exporter reads v0.3 candidate artifacts and creates human-review CSVs that preserve source-safety statuses, manual flags, gaps, caps, tags, source warnings, and review-only pick-zone context.

## How To Run

From the repo root:

```powershell
python scripts/rookie_framework/build_rookie_review_board_v03.py --strict
```

Optional arguments:

- `--input-root`: override the rookie local-export input root.
- `--output-dir`: override the output directory.
- `--strict`: fail on prohibited candidate input columns or market contamination blockers.

## Output Location

The default output directory is:

`local_exports/model_v4/rookie_framework_v02/review_board_v03/`

Expected files:

- `rookie_review_board_v03.csv`
- `rookie_review_board_premium_review_v03.csv`
- `rookie_review_board_round2_v03.csv`
- `rookie_review_board_5_04_watchlist_v03.csv`
- `rookie_review_board_manual_flags_v03.csv`
- `rookie_review_board_remaining_gaps_v03.csv`
- `README_ROOKIE_REVIEW_BOARD_V03.md`

These generated outputs are local-only and must not be committed.

## Validation

Step 2 validation should run:

```powershell
git status --short
git diff --check
python -m pytest tests/test_rookie_review_board_v03.py -q
python scripts/rookie_framework/build_rookie_review_board_v03.py --strict
git diff -- docs/rookie_framework/ scripts/rookie_framework/ tests/test_rookie_review_board_v03.py
```

The tests use temporary fixture data and do not depend on user local exports.

## What It Enables Next

Step 2 enables human review of the v0.3 candidate evidence in a consistent format. It makes premium-pick review, Round 2 review, 5.04 watchlist review, manual questions, and remaining gaps easier to inspect.

## What It Does Not Enable Yet

Step 2 does not enable:

- final rookie rankings;
- production rankings;
- private score changes;
- production formulas;
- Streamlit or app display;
- rookie probabilities;
- rookie probability bands;
- app-readable rookie outcome columns;
- outcome-column files;
- veteran outcome-head usage;
- promoted model artifacts;
- commits to `data/` or `local_exports/`.

## Recommended Step 3

Create a shadow rookie ranking export only after review-board outputs are green, still no production ranking/app promotion and no probabilities/bands.

Step 3 must remain rookie-only and should stop on market/rank/projection contamination, unexpected ranking/private-score changes, row-count breaks, unresolved premium-pick source conflicts, probability/band creation, app wiring, outcome-file changes, or any attempt to route rookies through veteran outcome heads.
