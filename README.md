# Niners Dynasty: War Room

Private, local-first fantasy football decision engine for the Las Vegas Enginerds keeper/dynasty hybrid league.

V1 is the Drop Deadline Command Center. It focuses on each roster's league-rank
top-five release pressure, keeper/drop decisions, pick values, trade leverage,
and league pressure using local CSV/SQLite snapshots.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Initialize Database

```powershell
python scripts/init_db.py
```

## Load Sample Data

```powershell
python scripts/load_data_pack.py sample_data/2026_pre_declaration
```

## Run App

```powershell
streamlit run app/main.py
```

## Run Tests

```powershell
pytest
```

## Lint

```powershell
ruff check .
```

## Generate Veteran Outputs

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-veteran-model.ps1 --data-dir sample_data/veteran_model_v1 --output local_exports/veterans/veteran_model_outputs.csv
```

Generated model outputs belong in `local_exports/`. Keep source CSV fixtures,
registries, notes, and overrides under version control; regenerate outputs when
inputs change.

## Real Data Templates

Header-only templates live in `templates/real_data_inputs/`.

- `data_pack/` is the app-ready data pack shape.
- `veteran_model/` is the normalized veteran model input shape.
- `rookie_model/` is the rookie source/normalization input shape.
- `public_sources/` is the raw projection, market, role, injury, and bio
  staging shape used before any public data becomes normalized model input.

Copy templates into `local_exports/` before filling real league data. The
committed templates stay empty so they remain clean schema references.

## Draft-Pressure Workflow

Use the app in this order.

1. Refresh Sleeper on Import Review.
2. Merge league ranks from the local league-rank text/PDF extraction.
3. Build a new data pack from the refreshed Sleeper snapshot plus merged league ranks.
4. Fill public-source intake files or normalized veteran feature inputs from local exports.
5. Validate Sources & Overrides before converting raw source rows into feature scores.
6. Score the model from local normalized inputs.
7. Review Import Review readiness:
   - `data_ready`: rosters, picks, and league ranks can be inspected.
   - `model_ready`: keeper/drop/trade outputs are real, not placeholders.
   - `decision_ready`: the selected pack can drive money decisions.
8. Use War Board as the main decision surface.
9. Use Team for the Niners-specific Roster's League-Rank Top Five explanation.
10. Use League Intel for opponent pressure.
11. Use Rankings to inspect the draftable pool before or during the offline draft.
12. Use Draft Board to run mocks, enter live picks, undo mistakes, and save/load scenarios.
13. Use Sources & Overrides to audit source matches and manual feature-level overrides.
14. Use Draft Freeze when the draft board is locked.

## Mock And Live Draft Workflow

Use two pages during the offline mixed draft.

1. Open Rankings first.
2. Confirm the pool only contains draftable rookies, released veterans, free agents, and manual additions.
3. Leave Availability on `available` during the draft; drafted players are hidden by default.
4. Open Draft Board.
5. Use the pick grid as the live source of truth.
6. When a player is selected in the real room, choose the pick, search the player, and click Mark Drafted.
7. When the current pick is yours, use the on-clock panel and Best Remaining By Position.
8. Use Undo Last for quick mistakes.
9. Use Replace Pick only when correcting a prior pick.
10. Use Reset Mock only after checking Confirm reset.
11. Save mocks before leaving the page; unsaved mock changes are intentionally flagged.
12. Download Draft Board CSV or Remaining Pool CSV from Draft Backups when you want an emergency local copy.
13. Load or duplicate mocks from Mock Save / Load without changing source data packs.

Draft Board state is session-local until saved as a mock JSON under `local_exports/mock_drafts/`.
It never mutates the active data pack or model outputs.

## Trust Labels

The app uses the same trust labels across the sidebar and decision pages:

- `Blocked`: fix Import Review errors before using boards.
- `Inventory Only`: rosters, picks, and each Roster's League-Rank Top Five list
  are visible, but model recommendations are hidden because outputs are
  placeholders.
- `Review Only`: scored outputs exist, but a warning, coverage gap, source issue, or diff still needs human review.
- `Decision Ready`: the selected pack passes the current readiness contract and can drive War Board decisions.

## Historical Replay

Historical Replay is a calibration-only page. It compares actual past rookie draft
notes with frozen as-of model replay rows and later outcome labels.

Use it to answer process questions such as:

- Did the model find rookie values before the room did?
- Did QB/TE suppression avoid bad picks in this format?
- Did the model miss hits because of missing data or a bad formula?
- Did released-veteran opportunity cost change the right picks?

Guardrails:

- Do not use future knowledge to create historical model scores.
- Keep later outcome labels separate from model inputs.
- Treat missing replay rows as calibration gaps, not failures.
- Historical replay never feeds current War Board, Team, Rankings, or Draft Board scores.

## Research Archives

The model-policy source documents live under `docs/codex`.

- Rookie research phases 1-5: `docs/codex/rookie_model_research`
- Veteran, asset, forced-release, source, and audit phases 6-10:
  `docs/codex/veteran_asset_research`

Phase 10 is the controlling caution layer for the veteran/asset work: exact
coefficients are model-design defaults unless explicitly supported by the audit.

## Draft-Day Freeze

The freeze workflow is local-only and deliberate. It does not refresh Sleeper, merge ranks, rebuild a pack, or mutate the active pack.

Before freezing:

1. Confirm `data_ready`, `model_ready`, and `decision_ready` on Import Review.
2. Confirm War Board is showing real scores, not placeholder inventory.
3. Confirm Team and League Intel explain the same Required Top-Five Release
   Slot candidates.
4. Confirm Rankings and Draft Board pick values, availability, and release targets.
5. Confirm Sources & Overrides has no unaudited active override.

When you click Freeze Active Pack:

- The active data pack is copied into `local_exports/draft_freezes/<freeze_id>/data_pack_backup`.
- `model_outputs.csv` is copied into `model_output_backup`.
- Key boards are exported to CSV in `board_exports`.
- `decision_readiness_checklist.csv`, `pack_health_checks.csv`, `pack_coverage_report.csv`, and `trust_status.csv` are exported with the boards.
- `model_run_metadata.json` records snapshot, trust status, readiness, model versions, placeholder count, exported boards, and no-mutation policy.
- `DRAFT_DAY_README.txt` summarizes the freeze, trust status, next action, and no-refresh policy.
- `FREEZE_LOCK.txt` marks the folder as draft-day read-only.

After freezing, do not refresh or rebuild for that draft unless you intentionally create a new freeze ID and re-review readiness from the top.

## V1 Guardrails

- Runtime must use local snapshots, not live APIs.
- League Rank controls the summer Roster's League-Rank Top Five release rule.
  This means the five highest league-ranked players on each roster, not league
  ranks 1-5 overall. League rank is a rule signal, not player quality.
- War Board is the main LVE decision surface.
- Trade Liquidity estimates public-market tradability. It is not private football value.
- Keeper Score estimates long-term hold value.
- Drop Score estimates who should be released or shopped.
- Pick Value uses a 1,000-point local scale.
- Placeholder model outputs are review-only. They can show roster and league-rank inventory, but not final recommendations.
- Public-source intake rows are review-only until they are normalized into veteran
  feature scores and the model is regenerated.
- Manual overrides may change feature scores only and must have provenance, reason, source key, approver, and a matching audit note.
