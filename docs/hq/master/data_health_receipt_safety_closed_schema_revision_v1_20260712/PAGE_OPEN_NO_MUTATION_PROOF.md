# Page Open No-Mutation Proof

The real Streamlit pages were opened through `AppTest` for each state below:

- valid latest;
- missing latest;
- corrupt latest;
- unsupported schema;
- oversized receipt;
- duplicate-key receipt;
- invalid-type receipt with recomputed integrity.

Both `app/pages/24_refresh_data_v1.py` and
`app/pages/28_settings_data_health_v1.py` passed every state: `14 passed in 7.80s`.

Before and after each open, the test captured the entire controlled root: directory entries,
filenames, file lengths, SHA-256 hashes, and `mtime_ns`. A protected source/production
sentinel was included in the same snapshot. All snapshots were identical. Every refresh
runner was replaced by a fail-fast spy; the call list remained empty. No quarantine,
archive, backup, latest, source, or production mutation occurred.

The inherited two-route smoke also passed `2/2` without a receipt write or refresh. Passive
render text tells the user that read-only inspection made no change and explicit maintenance
is required.
