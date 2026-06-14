# Rookie Framework v0.3 Step 3 Shadow Ranking README

## What Step 3 Created

Step 3 adds a rookie-only shadow export:

- `scripts/rookie_framework/build_rookie_shadow_ranking_v03.py`
- `tests/test_rookie_shadow_ranking_v03.py`
- `docs/rookie_framework/ROOKIE_SHADOW_RANKING_EXPORT_20260613.md`
- `docs/rookie_framework/README_ROOKIE_FRAMEWORK_V03_STEP3_SHADOW_RANKING.md`

The exporter reads Step 2 review-board outputs and creates local-only shadow ordering CSVs. Every row is marked `promotion_status=shadow_only` and `production_allowed=no`. The shadow rows also carry Step 2 `tag_summary` context so role/archetype rationale is visible during audit.

## How To Run

From the repo root:

```powershell
python scripts/rookie_framework/build_rookie_shadow_ranking_v03.py --strict
```

Optional arguments:

- `--input-root`: override the Step 2 review-board input directory.
- `--output-dir`: override the shadow export output directory.
- `--strict`: fail on prohibited private input columns.

## Output Location

Default output directory:

`local_exports/model_v4/rookie_framework_v02/shadow_ranking_v03/`

Expected files:

- `rookie_shadow_ranking_v03.csv`
- `rookie_shadow_ranking_premium_v03.csv`
- `rookie_shadow_ranking_round2_v03.csv`
- `rookie_shadow_ranking_5_04_watchlist_v03.csv`
- `README_ROOKIE_SHADOW_RANKING_V03.md`

These files are local-only and must not be committed.

Each CSV row includes `tag_summary` as review-only role/archetype context. The field is not a production score, probability, band, or app-readable recommendation.

## Validation

Recommended validation:

```powershell
git status --short
git diff --check
python -m pytest tests/test_rookie_shadow_ranking_v03.py -q
python scripts/rookie_framework/build_rookie_review_board_v03.py --strict
python scripts/rookie_framework/build_rookie_shadow_ranking_v03.py --strict
git diff -- docs/rookie_framework/ scripts/rookie_framework/ tests/test_rookie_shadow_ranking_v03.py
```

If pytest is unavailable, run the direct test harness and report that pytest was unavailable.

## What It Enables Next

Step 3 enables a shadow-only human review of deterministic rookie ordering. It can support later adversarial audit of whether the review metadata is coherent enough for any future, explicitly approved promotion discussion.

## What It Does Not Enable Yet

Step 3 does not enable:

- production ranking changes;
- final rookie rankings;
- private score changes;
- production formula changes;
- Streamlit/app display;
- rookie probabilities;
- probability bands;
- app-readable rookie outcome columns;
- outcome-column files;
- veteran outcome-head usage;
- commits to `data/` or `local_exports/`.

## Recommended Next Rookie-Only Task

Run a Step 3 adversarial audit of the shadow export before any future promotion discussion. The audit should verify row markers, no prohibited private inputs, no app/outcome/veteran touches, stable row counts, and no unresolved premium-pick source conflicts being hidden by the shadow order.
