# Known caveats and unsupported persistence

- Actual Explorer identity, Desktop, and LocalAppData ownership are unresolved from the sandbox.
- The legacy Data Health latest receipt is invalid (`CORRUPT`); real migration/start must remain blocked.
- Stable canonical checkout `C:\NWR\Niners-War-Room-V1` is absent.
- No real Desktop or Start Menu shortcut exists.
- Chrome/Edge app mode and owned-tree cleanup are code/focused-test proven, not GUI-proven.
- Default-browser fallback cannot deterministically own or observe the user's normal browser window; explicit Stop is authoritative.
- Trading Lab scenarios remain `POST_V1_PERSISTENCE_NOT_SUPPORTED`.
- Streamlit selectors, transient filters, and other labeled session state reset by design.
- LocalData pack is unavailable and remains an exact exit-4 blocker.
