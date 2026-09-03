# NWR desktop launcher/data-root inventory (2026-09-03)

Mechanical inventory (Desktop + Start Menu shortcuts, AppData roots),
read-only, before any consolidation decision. No launchers modified.

| Launcher | Target | Tauri/product identity | Data root | Classification |
|---|---|---|---|---|
| Niners War Room — Redraft | `...\Niners War Room — Redraft\nwr-redraft-war-room.exe` | `com.ninerswarroom.redraft` | `%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\` | **CANONICAL_CURRENT** — this ran the real KHA draft |
| Niners War Room — Dynasty | `...\Niners War Room — Dynasty\nwr-dynasty-war-room.exe` | `com.ninerswarroom.dynasty` | `%LOCALAPPDATA%\com.ninerswarroom.dynasty\` | CANONICAL_CURRENT for Dynasty (separate lane, not touched) |
| NWR Legacy — Streamlit | PowerShell → `C:\NWR\Niners-War-Room-V1\scripts\NWR Desktop Commands.ps1` | none (Streamlit, own git repo) | `C:\NWR\Niners-War-Room-V1\local_exports\`, `data_packs\` | LEGACY_FALLBACK — has its own Start Menu install/uninstall/backup/restore-dry-run/status/recover-data-health shortcut family. Root `AGENTS.md`/`MODEL_SPEC.md`/`RUN_POLICY.md`/`TASK_QUEUE.md` in the current `draft-upgrade-hq` worktree are near-identical boilerplate to this repo's files — inherited/stale, not describing the current Tauri architecture. |
| NWR — KHA HIGH STAKES DRAFT | `...\kha-espn-desktop-recon\desktop\LAUNCH_KHA_HIGH_STAKES_DRAFT.bat` | (dev worktree, same Tauri app) | same `com.ninerswarroom.redraft` root as canonical | STALE_DUPLICATE — points at worktree `kha-espn-desktop-recon`, branch `emergency/kha-draft-room-correctness-v1-20260902` @ `521d99fd`, the exact commit `draft-upgrade-hq` was cut from before this session's work. Should eventually repoint to the canonical worktree/build once this lane's branch is adopted; not changed tonight (out of this lane's push/merge authority). |
| `NinersWarRoom` AppData root (no shortcut found pointing directly at it) | n/a | none identified | `%LOCALAPPDATA%\NinersWarRoom\` (`backups/`, `browser-profile/`, `config/`, `data/`, `logs/`, `recovery/`) | UNKNOWN — `browser-profile` suggests an older webview/browser-shell wrapper, likely predating the Redraft/Dynasty Tauri split. Not investigated further; flagging rather than guessing. |

## Consolidation target (long-term, not tonight's scope)

Per the owning brief: one owner-facing "Niners War Room" application, with
KHA / Fantasy Gamers / NWR PURE as **league profiles** inside Redraft, not
separate permanent apps. The canonical runtime data root is confirmed
(`%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\`, matches the
checkpoint fix already shipped this session). Legacy Streamlit may stay
labeled recovery/legacy until separately retired. No state was migrated
or launchers changed -- this is inventory only, so a consolidation
decision can be made with full information rather than guessed at.
