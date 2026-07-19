# NWR V1 RC1 runtime targeted revision report

This successor is based directly on RC commit `c380956dcab863dd7f921ec237506c08f46990b8`. It changes only Draft Cockpit route registration, a test-owned Streamlit lifecycle runner, their direct regression tests, and this packet.

The route authority is `SUPPORTED_HIDDEN_ROUTE`. Streamlit treats a page declared `default=True` as the root page and ignores its configured named URL. The revision therefore gives `/` a separate hidden default wrapper and keeps `pages/44_draft_cockpit_root.py` as a non-default named hidden route. `/draft-cockpit-root` now remains on that URL and renders the canonical `Draft Cockpit` H1 without a Page Not Found dialog.

The reported CPython fatal was not reproducible in three bounded unmodified-RC attempts. Those attempts did deterministically reproduce the route defect. One forced child-termination probe and two ordinary close paths produced no semaphore fatal. A later ad-hoc full-matrix console shutdown released the listener but retained its interpreter until explicit cleanup, confirming that teardown ownership was not reliable enough.

The narrow runtime correction is a test launcher that invokes `python -m streamlit` without a shell/uv wrapper, claims a Windows process group, refuses an occupied port, supports a ready/shutdown handshake, closes the browser before sending `CTRL_BREAK_EVENT`, treats forced cleanup or nonzero exit as failure, verifies port release, and scans unsuppressed stdout/stderr for all reported fatal markers.

Pre-commit candidate evidence: 180/180 endpoint checks; three consecutive 34/34 complete browser/runtime cycles plus three clean second starts; focused route/UI 76; Data Health/passive read 107; CSV/trust security 300; tracked UI contract 26; security automation 20/20; LocalData exact exit 4; compilation and changed-file Ruff green; whole-tree Ruff differential unchanged at 4,443 findings.

The temporary clean candidate commit's Hermetic gate passed bootstrap 13/13 and security 20/20, then reported 2,626 passed and one failure. The sole failure is the existing Data Health path-name heuristic treating the required tracked documentation `...runtime.../MANIFEST.json` as runtime state. Because changing Data Health behavior is outside this lane's hard scope, post-commit repeatability stopped under fail-fast and the final verdict is red. The branch was then soft-reset to RC so no failed-gate successor commit remains; all candidate changes are staged. See `EXECUTIVE_VERDICT.md` and `VALIDATION_RESULTS.md`.
