# Deprecation Message Differential

Result: PASS; no new message from new code.

Both clean live HQ (`250c28853a4bc175b2702e206e68f49560c4e6e0`) and source (`46c19263df84015352e7a8bc6728507f48dc69ba`) were opened with Streamlit `AppTest.from_file(...).run(timeout=30)` for:

- `app/pages/24_refresh_data_v1.py`
- `app/pages/28_settings_data_health_v1.py`

Each run emitted 11 `Please replace use_container_width with width` runtime messages: one executed occurrence on Refresh Data and ten on Settings / Data Health. Static locations are the pre-existing `use_container_width=True` calls in those pages (source lines 217, 220, 223, 226, 253, 270, 276, 284; and 59, 69, 110, 158, 192). Not every static branch executes during page-open smoke.

The new component uses `st.dataframe(..., width="stretch", ...)` at `app/components/refresh_recovery_panel.py:30`, which is the supported replacement and emits no deprecation message. Existing warnings were intentionally not repaired.
