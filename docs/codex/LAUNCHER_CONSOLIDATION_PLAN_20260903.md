# Launcher/product consolidation — bounded migration plan (section 21)

Builds on the real, already-completed inventory in
`docs/codex/LAUNCHER_INVENTORY_20260903.md` (unchanged, read-only). No
launcher was renamed, deleted, or modified this pass; no data root was
migrated.

## Target state (already confirmed, unchanged from the inventory)

One owner-facing launcher — **Niners War Room — Redraft**
(`com.ninerswarroom.redraft`, data root
`%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\`) — with KHA /
Fantasy Gamers / NWR PURE / future leagues as **profiles inside it**,
not separate apps. This target already matches how the app's own
profile system already works today (`redraft_engine_v1_service.py`'s
`LeagueProfile`/multi-profile store) — the consolidation is about
launcher/shortcut surface area, not a data-model change.

## Why no candidate shortcut was created tonight

The directive's own phrasing is conditional: *"If low-risk launcher
creation can be proven reversible, a candidate shortcut may be
created."* Checked before acting, not assumed:

- No built executable for this worktree's branch exists anywhere on
  this machine (`desktop/**/target/**/*.exe` — none found). Pointing a
  new shortcut at *something real* would require a fresh Tauri/Rust
  release build first.
- A Tauri release build is exactly the kind of heavyweight operation
  the addendum's own resource-discipline section calls out
  ("Serialize heavy operations... at most one heavyweight… Tauri build…
  at a time," on "a Windows machine that has experienced resource
  exhaustion before"). Running one unattended, with no one available to
  notice and recover from a resource problem, is a real risk for a task
  this directive itself marks as conditional/optional.
- "Provably reversible" cannot honestly be claimed for a shortcut
  pointing at a binary that has never been built and run once —
  reversibility of the *shortcut file itself* is trivial (delete it),
  but I cannot verify the *launch actually works* without running the
  build and opening the app, which is the heavyweight, unattended-risk
  step above.

Skipping the literal shortcut creation is the bounded, safe choice
here — not an early stop, since the actual useful output (the concrete,
step-by-step recipe below) is fully prepared and ready to execute in
minutes once someone is available to watch a build.

## Exact recipe for the next session (or the owner) to execute

1. From `C:\Users\codex-agent\orca\workspaces\Niners-War-Room\draft-upgrade-hq\desktop`,
   run the existing Tauri release build for the `redraft` app (the
   repo's own build script/`npm run tauri:build` equivalent — confirm
   the exact command against `desktop/package.json`'s scripts before
   running; not re-verified here to avoid implying a build was tested).
2. Confirm the produced executable launches and reaches the same
   `com.ninerswarroom.redraft` bootstrap the canonical launcher already
   uses (same data root, so no new profile/data state is created).
3. Create a Desktop/Start Menu shortcut named exactly
   **"Niners War Room — Draft Upgrade Preview"** pointing at that
   executable. Do not reuse or overwrite any existing shortcut's icon,
   target, or name.
4. Rollback, if ever needed: delete only that one new shortcut file.
   Nothing else on the machine changes — the app it launches shares the
   canonical `com.ninerswarroom.redraft` data root already in daily use,
   so there is no separate data root to clean up, and no other
   launcher's target/icon/name was touched to create this one.

## What remains explicitly out of scope, per the directive itself

- No data-root migration without explicit owner review (none proposed
  here — the canonical root is already shared).
- No renaming, deleting, or retargeting of the KHA/Legacy Streamlit/
  Dynasty launchers already inventoried.
- Deciding when the Legacy Streamlit launcher family is finally retired
  is the owner's call, not something this pass proposes a timeline for.
