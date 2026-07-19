# Browser app mode and lifecycle

Chrome is preferred, Edge second, and the default browser is the final fallback. Chrome/Edge receive `--app=http://127.0.0.1:8520/`, `--user-data-dir=<launcher browser-profile>`, `--disable-background-mode`, `--disable-extensions`, `--no-first-run`, and `--no-default-browser-check`. The normal user profile is never selected.

The supervisor remains alive while its launcher-owned app-mode process remains alive. Closing that process requests a graceful Streamlit shutdown. The explicit Stop command is authoritative. Default-browser fallback cannot reliably observe the last window, so users use Stop; this is the documented bounded fallback caveat.

Installed candidates detected in this environment are used without extension installation or browsing-data capture. Browser command construction and isolated profile paths were tested; a real GUI window was not opened because installation identity remained unresolved.
