# Mission

> **LEGACY NOTICE (2026-09-10):** This document describes the original
> dynasty/keeper "Drop Deadline Command Center" concept. It predates, and
> does not mention, the live desktop Redraft in-season product (weekly
> lineup, waivers, trades, live Sleeper leagues) that exists in this repo
> today. Kept unedited below as the historical record. See
> `PRODUCT_ARCHITECTURE.md` for the current product.

Build Niners Dynasty: War Room V1, a local-first Drop Deadline Command Center for one league and one primary user: the Niners co-owner.

The app should answer:

- Who are the Niners' official top five players?
- Which top-five player is the default release if nothing changes?
- Which players should be kept, dropped, or shopped?
- Which trade options save value before Roster Declaration Day?
- Which teams are under keeper pressure?
- Which players are likely to enter the draft pool?
- How valuable are current and future picks?

V1 should be ugly-but-powerful: deterministic models, CSV import, SQLite storage, and table-first Streamlit screens.
