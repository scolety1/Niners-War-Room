# Niners Dynasty: War Room

Private, local-first fantasy football decision engine for the Las Vegas Enginerds keeper/dynasty hybrid league.

V1 is the Drop Deadline Command Center. It focuses on official top-5 release pressure, keeper/drop decisions, pick values, trade leverage, and league pressure using local CSV/SQLite snapshots.

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

## V1 Guardrails

- Runtime must use local snapshots, not live APIs.
- Official Rank controls league rules.
- War Score controls Niners strategy.
- Market Score estimates trade perception.
- Keeper Score estimates long-term hold value.
- Drop Score estimates who should be released or shopped.
- Pick Value uses a 1,000-point local scale.
