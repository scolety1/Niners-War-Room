# Architecture

## Product

Niners Dynasty: War Room is a private local-first fantasy football decision engine for the Las Vegas Enginerds keeper/dynasty hybrid league. V1 is the Drop Deadline Command Center: it imports local league snapshots, validates them, stores them in SQLite, and exposes deterministic tables for Niners keeper/drop, top-five forced-release, pick value, trade leverage, and league pressure decisions.

## Users

The primary user is the Niners co-owner. Secondary users are future reviewers of the local data workflow who need to understand why a recommendation was produced.

## System Boundaries

Inside V1:

- Streamlit local dashboard
- Local CSV data packs
- Local SQLite database
- Deterministic scoring formulas
- Test-backed validation and import logic

Outside V1:

- Mandatory live APIs
- Web scraping
- Production deployment
- Auth, payments, accounts, multi-user hosting, and customer data
- Complex ML or black-box advice

## Runtime

Runtime is local-only:

```text
CSV snapshot -> validation -> SQLite -> Streamlit pages
```

The app must not require network access during keeper, trade, or draft decisions.

## Data Model

SQLite mirrors the canonical CSV files:

- players
- teams
- owners
- rosters
- official_rankings
- future_picks
- pick_values
- market_values
- player_features
- model_outputs
- owner_notes
- metadata_sources
- import_errors

Generated SQLite databases live under `data_packs/` and are ignored by git unless explicitly approved.

## API Contracts

V1 has no runtime web API contract. Import contracts are CSV schemas documented in `DATA_MODEL.md` and enforced by validators.

Future optional API collectors may create new local snapshots, but they are not part of runtime and require explicit approval before implementation.

## Security Model

No secrets are required for V1. No auth system is required. No production customer data is used. All external services are disallowed at runtime.

## Dependencies

Approved bootstrap dependencies:

- Python 3.12+
- Streamlit
- SQLite standard library
- pandas
- pydantic
- numpy
- pytest
- ruff

Package/dependency changes are blocked by default and require `DEPENDENCY_PROPOSAL.md` plus `DEPENDENCY_APPROVAL.md`.

## Deployment Model

No deployment in V1. Run locally with:

```powershell
streamlit run app/main.py
```

## Open Questions

- Exact Roster Declaration Day date is configurable and unknown.
- Dirt Devils owner mapping needs verification.
- Final roster packet import format may require additional CSV cleanup rules.
