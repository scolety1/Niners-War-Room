# Run Policy

> **LEGACY NOTICE (2026-09-10):** The section below described the
> original Streamlit/CSV-pack-only prototype and is now **inaccurate**
> for the live desktop Redraft product. The desktop app (`desktop/apps/
> redraft`, `src/desktop_api/server.py`, `src/application/
> desktop_facade.py`) makes real, live network calls -- Sleeper (league
> state, rosters, weekly projections) and FantasyPros (K/DST consensus)
> -- whenever an owner has an active Sleeper-imported league. This was
> never a secret regression: it is disclosed, owner-governed, and covered
> by real fail-safe/health machinery (see `DATA_AUTHORITY.md`). Kept below
> unedited as the historical record for the original CSV-pack/dynasty
> product line, which this policy still genuinely governs. The current,
> accurate runtime policy for the whole product is in
> `PRODUCT_ARCHITECTURE.md` and `DATA_AUTHORITY.md`.

## Legacy: original CSV-pack/dynasty product line

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

## Current: live desktop Redraft product

- Live, owner-governed network calls ARE part of this product for a
  Sleeper-imported league: league state/rosters (`SleeperHttpClient`),
  weekly projections (`weekly_projection_provider_service.py`, an
  approved temporary/stopgap Sleeper adapter), and K/DST consensus
  (`FantasyProsConsensusClient`, requires an owner-supplied API key).
  None of these write back to Sleeper or FantasyPros -- every in-season
  facade method returns `"writeBehavior": "NO_SLEEPER_WRITES"` (or the
  K/DST-specific variant) and this is enforced by convention, not by a
  network restriction.
- Every live call has a real, disclosed fail-safe: schema validation,
  coverage-collapse detection, a short-TTL cache, and a stale-snapshot
  fallback bounded to 36 hours, always labeled `STALE` when reused -- see
  `weekly_projection_provider_service.py` and `DATA_AUTHORITY.md`.
- Production deploys, auth, and payment/customer-data integrations remain
  out of scope, unchanged from the legacy policy above.
- The original CSV-pack/dynasty product line (draft legality, historical
  backtest, `marginal_roster_utility_v2`, Team Score V2/Equity V2/Raw
  Action Value) remains governed by the legacy policy above -- frozen
  data packs, no live calls -- and is untouched by this section.
