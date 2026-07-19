# Windows desktop launcher report

Verdict: `BLOCKED_NWR_DESKTOP_LAUNCHER_EXISTING_PERSISTENCE_NOT_AVAILABLE`.

The launcher implementation is complete and synthetically validated, but installation is blocked. The existing primary-worktree Data Health receipt returned `CORRUPT` from the accepted read-only schema validator and has no valid backup. The launcher preserves those bytes, refuses automatic migration/restoration, and does not create the real desktop shortcut. Explorer ownership was also unavailable to the sandbox identity, so the tested one-click installer remains the safe handoff.

Accepted base commit/tree: `dc399a8c2ed5d77d9802d98c215a12cbe594d7d7` / `e6f98339bf7172b45b78d94dfed390559856f899`.

The implementation adds no product behavior. It uses the accepted Streamlit command and lifecycle helper, port 8520, Python 3.12+, `pythonw.exe`, a single ownership lock, Chrome/Edge app mode with a dedicated profile, five bounded launcher snapshots, validated junctions for the two repository-relative state families, and existing service-owned roots for draft and Development Lab state.
