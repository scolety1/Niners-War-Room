# Preview bootstrap -- sidecar companion-binary fix (section 1)

## Root cause

`desktop/apps/redraft/src-tauri/tauri.conf.json`'s `externalBin` declares
`../../../binaries/nwr-desktop-api` -- Tauri v2 requires the binary to
exist at `<that path>-<target-triple>.exe` before it will start, in dev
mode as well as a release build. On this worktree, `desktop/binaries/`
held only a `.gitignore` (the binary itself is gitignored -- it's a
~150MB build artifact, correctly never committed). Nothing had ever run
the build for THIS worktree, so the file did not exist -- the exact
failure the owner saw.

## Source project / expected output / target triple

- Source: `scripts/run_nwr_desktop_api.py` (the same real, unmodified
  entrypoint `DesktopBackendFacade`/`create_desktop_api_server` module
  this whole session's backend work has been testing against).
- Build script (already existed, canonical):
  `desktop/scripts/build-python-sidecar.ps1`, wired to
  `npm run sidecar:build` in `desktop/package.json`.
- Expected output:
  `desktop/binaries/nwr-desktop-api-x86_64-pc-windows-msvc.exe`
  (target triple `x86_64-pc-windows-msvc`, matching this machine and the
  exact filename the owner's error message named).
- The script already verifies/builds deterministically: it skips
  rebuilding if an existing output is >1MB and newer than every input
  file (script itself, entrypoint, `pyproject.toml`, every `src/**/*.py`),
  runs a `--help` smoke test on the freshly-built binary before
  publishing it, and writes a SHA-256 receipt next to the binary.

## Why it was absent / other worktrees

Two other NWR worktrees on this machine
(`nwr-desktop-experience-v1-20260811`,
`nwr-desktop-owner-reconciliation-v1-20260814`) already have a built
copy -- but both predate this branch's backend work by weeks. **Not
copied**: the binary embeds this exact worktree's `src/` tree
(`--paths $repoRoot` in the build script); a binary built from a
different commit would silently reproduce the same "stale build"
problem already diagnosed for the installed shortcut. It must be built
from this HEAD, and only from this HEAD.

## Fix applied

Ran `desktop/scripts/build-python-sidecar.ps1` from this worktree
(requires `uv`, confirmed present). Build succeeded:
`desktop/binaries/nwr-desktop-api-x86_64-pc-windows-msvc.exe`
(149,347,056 bytes), SHA-256
`f4de73f8c97891824a8d55cdf3945295c1d4a75ad3f522df5d48238eeb53def9`,
smoke-tested by the script itself before being published.

`desktop/launch-draft-upgrade-preview.bat` (the temporary preview
launcher created last session, untracked in git by design) now runs
`npm run sidecar:build` before `npm run tauri:redraft` every launch --
the script's own freshness check makes this a fast no-op when the
binary is already current, and an automatic rebuild when this
worktree's source has changed since the last build. This is the
"deterministic local dev-bootstrap command" the directive asked for:
verify/build -> place at the exact expected resource path -> the
script's own smoke test + SHA receipt stand in for path/hash
verification -> then launch.

## Verification

`sidecar:build` exit code 0, smoke test (`--help`) passed inside the
script, SHA-256 receipt written. Not independently re-launched
end-to-end from this session (launching the Tauri GUI shell is a
foreground, interactive action for the owner, not something this
session runs on the owner's behalf) -- the owner should now be able to
double-click `NWR — DRAFT UPGRADE PREVIEW` (or run
`npm run tauri:redraft` from `desktop/`) and reach the actual
candidate UI instead of the prior resource-path failure.

## Dynasty / shortcut scope

Not touched. Dynasty's own `externalBin` points at the same
`nwr-desktop-api` filename (`desktop/apps/dynasty/src-tauri/tauri.conf.json`)
and would need its own `sidecar:build` run only if/when the owner
launches a Dynasty dev build from this worktree -- not attempted here,
out of scope for this Redraft-focused directive. No existing desktop
shortcut was created, deleted, or repointed.
