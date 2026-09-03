# Historical redraft replay — data adapter (section 18)

Code: `src/services/historical_replay_data_adapter_service.py`. Tests:
`tests/test_historical_replay_data_adapter_service.py`, 20/20 passing.
Not imported by `desktop_facade.py` or any frontend page (verified via
grep) — this is offline research infrastructure, not a live surface.

Consumer-side of `docs/codex/HISTORICAL_REPLAY_DATA_CONTRACT_20260903.md`.
Draft Upgrade HQ still does not implement the Dataset Research Engine —
`docs/codex/HISTORICAL_REPLAY_SUBSTRATE_INVENTORY_20260903.md` found no
real conformant dataset is buildable from data in this repo today, and
that has not changed this pass. What shipped this pass is the adapter
that would consume one once it exists.

## What's real and working

- **Schema validator** (`validate_schema`): every row must carry every
  required pre-draft field with a non-empty value, and every `*_as_of`/
  `draft_date` field must be a real, parseable ISO date.
- **Leakage validator** (`validate_leakage`), two independent checks:
  1. Column-name check via `BLOCKED_FEATURE_TOKENS` — a **deliberate,
     literal copy** of `scripts/build_backtest_dataset_v0.py`'s own
     tuple (reusing that established pattern rather than inventing a
     new one, per the data contract's own instruction; copied rather
     than imported because `src/services/` does not depend on
     `scripts/`). Any row column outside the declared pre-draft/outcome
     field set whose name contains a blocked token (`adp`, `projection`,
     `ranking`, etc.) is refused.
  2. Date check: `projection_as_of`/`adp_as_of` must be strictly before
     `draft_date`; `status_as_of` no later than `draft_date`;
     `outcome_as_of` (if present) no earlier than `draft_date`. This is
     the genuinely new check the contract calls for — column-name
     blocking alone cannot catch a legitimately-named field that is
     simply dated wrong.
- **Identity validator** (`validate_identity_completeness`): every real
  historical pick must resolve to exactly one `player_id` in the row set
  or carry an explicit `identity_status` — an undisclosed gap fails
  validation; a disclosed one (matching the live-draft UNMATCHED/
  K_DST_UNREPRESENTABLE convention already used elsewhere this session)
  does not.
- **Loader** (`load_historical_replay_dataset`): returns
  `HistoricalReplayUnavailable` — never a faked or backfilled dataset —
  when no rows are supplied or any row fails validation. This is the
  honest, expected result in this repo today.
- **Chronological splitter** (`chronological_split`): explicit
  season-to-split assignment only (the caller states which seasons go
  where — nothing guesses). Refuses overlapping assignments, refuses any
  dataset season left unassigned, and enforces train < validate < test
  chronologically. General chronological-split discipline, not a literal
  spec drawn from `docs/codex/CALIBRATION_PLAN.md` — that file states
  calibration principles, not split mechanics; its own contract citation
  was imprecise on this point.
- **Evaluation runner** (`run_replay_evaluation`): a real, working
  round-by-round snake-draft simulator that scores arbitrary
  caller-supplied strategy functions (a strategy is just "a function that
  orders available players") against realized weekly outcomes. It does
  not hardcode PLATFORM ADP / GREEDY NWR / STANDARD VBD / CURRENT NWR
  HEURISTIC / TEAM SCORE optimizer / CHAMPIONSHIP EQUITY optimizer
  internally — each of those six methodologies the contract names is
  just a strategy function a caller would register once real market/rank
  data for a historical season exists to build one from. Tested with a
  small, explicitly-synthetic fixture (never presented as real
  historical evidence) proving the mechanism itself is correct: a
  points-aware strategy outscores a points-averse one on realized
  outcomes.

## What is still not possible

Running this adapter against real historical data remains blocked on the
same substrate gap the inventory doc found: no season in this repo has
both a real full snake-draft result and a genuinely-dated pre-draft
projection/ADP board. That gap is outside this lane's scope to close.
