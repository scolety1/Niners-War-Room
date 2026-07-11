# Passive Adapter Review

Result: PASS.

`src/services/refresh_recovery_presentation_service.py` imports only collections interfaces, `dataclass`, and typing. It contains no filesystem, network, database, Streamlit, source, orchestrator, manifest, session-state, clock, or persistence API. It maps supplied mappings into frozen presentation records and returns tuples. Input immutability and deterministic repeated output are covered by focused tests.

It performs no I/O, source call, refresh call, manifest write, state mutation, source-admission calculation, new freshness calculation, identity/fallback matching, error suppression, data repair, timestamp repair, diagnostic-link invention, or automatic recovery action. Success requires an explicit existing signal (`refreshed is True`, `action_type=REFRESHED`, or `execution_status=SUCCESS/SUCCEEDED`); absence of an error is not success. Missing timestamps render `Not recorded` and are not invented.

Precedence preserves gated, skipped, unavailable, failed, stale, partial, success, and insufficient-information distinctions. Stale retained data is never marked current; partial is never promoted to full success; unknown evidence remains `NOT_ENOUGH_INFORMATION`.

`app/components/refresh_recovery_panel.py` renders only supplied frozen presentation objects inside a collapsed Streamlit expander. Render contains captions and a dataframe only—no button, link, callback, refresh/retry invocation, navigation, or mutation. Availability tokens clearly distinguish executable-control guidance, review-only guidance, information, and unavailable action.
