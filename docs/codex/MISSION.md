# Niners Dynasty: War Room Mission

Build a private, local-first fantasy football decision engine for the Las Vegas Enginerds keeper/dynasty hybrid league.

The V1 product is the Drop Deadline Command Center. It should help the Niners co-owner answer:

- Who are the Niners' current official top five players?
- Which top-five player should be released if nothing changes?
- Which players should be kept, dropped, or shopped?
- Which trade options can save value before Roster Declaration Day?
- Which other teams are under keeper pressure?
- Which players are likely to enter the draft pool?
- How valuable are current and future picks?

## Product Shape

This is not a generic fantasy football app. Build a table-first, deterministic Streamlit tool backed by local CSV snapshots and SQLite.

## Non-Negotiables

- Runtime must not require live APIs.
- Do not scrape websites.
- Do not make Sleeper or any external API mandatory.
- Do not hardcode current rosters as permanent truth.
- Do not overwrite old data packs.
- Do not implement complex ML in V1.
- Do not create a flashy UI before import/model correctness.
- Keep Official Rank, Market Rank, War Room Rank, and My Rank separate.
- If a league rule is unclear, make it configurable.

## V1 Priority

Correctness beats polish. The app should feel like a sortable command table, not a fantasy advice blog.
