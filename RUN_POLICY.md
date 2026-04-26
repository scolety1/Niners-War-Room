# Run Policy

This project is local-first.

Allowed at runtime:
- Read local CSV data packs.
- Read and write local SQLite databases.
- Display deterministic scores and recommendations.

Not allowed at runtime:
- Mandatory live API calls.
- Web scraping.
- Production deploys.
- Auth, payment, or customer-data integrations.

Data packs are frozen snapshots. Never overwrite an existing data pack; create a new dated folder instead.
