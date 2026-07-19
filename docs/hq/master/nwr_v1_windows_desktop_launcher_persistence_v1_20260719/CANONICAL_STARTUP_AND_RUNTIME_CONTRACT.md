# Canonical startup and runtime contract

- Entry point: `app/main.py`.
- Supported Python: 3.12 or newer. Resolved test runtime: `C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\python.exe`, Python 3.12.13, Streamlit 1.58.0.
- Normal hidden launcher: the sibling `pythonw.exe` runs `scripts\nwr_desktop.py start`.
- Exact Streamlit command: `python.exe -m streamlit run app/main.py --server.address 127.0.0.1 --server.port 8520 --server.headless true --browser.gatherUsageStats false`.
- Readiness: HTTP 200 at `http://127.0.0.1:8520/_stcore/health`.
- Root URL: `http://127.0.0.1:8520/`.
- Canonical hidden route: `/draft-cockpit-root`.
- Lifecycle authority reused: `scripts/streamlit_runtime_cycle.py` (`start_streamlit`, `wait_for_http`, `graceful_shutdown`, port release, fatal markers).
- Dependencies are verified, never installed automatically. Git is verified only for repository identity; the launcher never fetches, pulls, checks out, merges, commits, or pushes.
