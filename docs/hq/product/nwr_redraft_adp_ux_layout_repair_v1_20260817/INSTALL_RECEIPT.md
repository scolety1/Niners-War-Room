# Install receipt

- Installed app: `C:\Users\codex-agent\AppData\Local\Niners War Room — Redraft`
- Installed product version: `1.0.1`
- Build command: `npm.cmd run bundle:redraft`
- Package command: `npm.cmd run tauri:build --workspace @nwr/redraft-desktop -- --bundles nsis`
- Installer: `Niners War Room — Redraft_1.0.1_x64-setup.exe`
- Installation method: normal non-force NSIS upgrade.

Owner-state verification found 24 files both before and after installation/verification. The only file written after the pre-build check was the local runtime heartbeat, `state\runtime.json`; no profile, draft-board, provider/import-cache, ranking, projection, or Sleeper state was changed.
