# NWR Desktop Experience V1 — Build, Run, and Acceptance

## Prerequisites

- Windows 10 or 11
- Node.js 22.12 or newer
- Rust MSVC toolchain
- Microsoft C++ Build Tools
- `uv` for the reproducible Python sidecar build

The installed applications do not require Node.js, Rust, Python, `uv`, or internet access. The Windows installers carry the WebView2 offline installer.

## Frontend verification

From `desktop`:

```powershell
npm.cmd install
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
```

## Python contract verification

From the repository root, run:

```powershell
python -m pytest -q tests/test_desktop_application_api.py tests/test_desktop_http_api.py
```

## Rust verification

The two Tauri build scripts should be checked sequentially because they generate app-specific capability metadata:

```powershell
cargo fmt --all -- --check
cargo check -p nwr-desktop-runtime
cargo check -p nwr-dynasty-war-room
cargo check -p nwr-redraft-war-room
```

## Build the self-contained sidecar

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File desktop/scripts/build-python-sidecar.ps1
```

The script creates an isolated, lock-free build environment with explicit Python/PyInstaller and runtime dependency pins, emits the Tauri target-triple filename, validates `--help`, and writes a SHA-256 integrity receipt. Generated executables are build artifacts and are not committed.

## Build installers

From `desktop`:

```powershell
npm.cmd run bundle:dynasty
npm.cmd run bundle:redraft
```

The products have distinct names, binaries, identifiers, shortcuts, frontend bundles, API modes, ephemeral loopback runtimes, and LocalAppData namespaces. The root scripts delegate into the matching npm workspace before invoking Tauri so app-specific capability metadata cannot cross modes.

## Owner acceptance

### Product isolation

- Launching Dynasty never exposes Redraft navigation or state.
- Launching Redraft never exposes Dynasty navigation or state.
- Both applications may run concurrently.
- Wrong-mode API routes return `404`.
- Redraft draft mutations leave Dynasty resources and workspace state unchanged.

### Core Dynasty workflow

- Home loads the accepted 240-player Finished V1 board.
- Rankings, market disagreement, player detail, Rookie Review, Player Compare, Trade Lab, planning, draft preparation, and Data Health render without a Streamlit dependency.
- Market freshness and blocked evidence remain visible.
- Trade decisions retain their ordinal, source-separated service authority.

### Core Redraft workflow

- A clean state validates and installs the admitted 608-player projection snapshot without external access.
- Creating a profile also activates it.
- Rankings and tiers reflect that profile's scoring and roster demand.
- Draft and undo use the existing ordered player-ID draft-board document.
- The two explicitly blocked position-conflict rookies remain visible as blocked evidence and are not inserted into rankings.
- Multiple profiles remain inside Redraft only.

### Lifecycle and security

- Windows remain hidden until a fresh HMAC-authenticated, exact-mode local startup and health sequence succeeds.
- Python atomically binds an OS-assigned high port on explicit loopback; no external interface is eligible.
- Missing, malformed, replayed, or incorrect launch secrets and startup proofs fail closed.
- Listener handoff, PID/job/image verification, or adoption failure aborts launch; the host never scans for, reuses, or terminates unrelated processes.
- Launch secrets are absent from process arguments and environment and are written once to sidecar standard input.
- The API bearer is not transmitted until the sidecar proves possession of a distinct startup-proof key.
- Closing an app removes only its owned sidecar/job.
- A host crash cannot orphan the sidecar.
- Owner state resides outside immutable resources.
- Streamlit still launches as the fallback experience.

## Final hardened V1 evidence — 2026-08-13

- Python desktop/API tests: 46 passed; broader persistence/desktop suite: 90 passed.
- TypeScript: project check passed; Vitest 32/32; both production Vite builds passed.
- Rust: formatting, runtime tests, and sequential locked release checks passed for both applications.
- Sidecar SHA-256: `50d053617928250f82268610e68f2d060c8a7463f09f85a248f6cb1112c2246e`.
- Final MSI SHA-256: Dynasty `77544308486a4428a30bbf26d0518487ac59041edaf4d4ea0642e846eafe5470`; Redraft `f2c72a77b168978ddf72c4a6619bf61beb999fe34c5db8b57ec23ffe35aca467`.
- Final NSIS SHA-256: Dynasty `742135a237cf3c131f38091108815f9150fb319867b0a9ba2f4f387f5dc76812`; Redraft `f374f33e27e8e4e9047593fc02d2b9ccf723456586a728e651b0a558672b01cc`.
- Five concurrent Dynasty/Redraft launch/close cycles and abnormal host termination left no owned listener or sidecar behind; unrelated processes were never targeted.
- Owner replays passed for global veteran/rookie/blocked/pick search, rankings, Compare invalidation, the known seven-asset trade, saved trades, Rookie Review, My Board/decisions/backup, Planning persistence, and Redraft profile/scoring/duplicate/search/draft/undo/Cheat Sheet.
- Layout inspection at 720×560, 1024×576, 1280×720, 1366×768, 1440×900, 1920×1080, and 2560×1440 found no document-level horizontal overflow in either app.
