# Install receipt

The normal NSIS upgrade target is Redraft `1.0.3`. Before packaging, the installed owner-state manifest covered 24 files with SHA-256 `59F977866B777F4FE345E9E1B4BDAB62B01B1D040A2F015443448D773CD34C18`. The version increment is required for Windows to recognize this as a normal upgrade.

The preliminary 1.0.2 package was installed successfully, then superseded before commit by the final 1.0.3 package that includes the Disabled/use FFC compatibility fix.

- Build commands: `npm.cmd run bundle:redraft`; `npm.cmd run sidecar:build`; `npm.cmd run tauri:build --workspace @nwr/redraft-desktop -- --bundles nsis`.
- Interim installer: `Niners War Room — Redraft_1.0.2_x64-setup.exe`, SHA-256 `52B18193CC13583D2DF1FA4C56D585492925333C4482E308E6DB3695B83BCE2E`, normal silent NSIS upgrade exit code 0.
- Final installer: `desktop/target/release/bundle/nsis/Niners War Room — Redraft_1.0.3_x64-setup.exe`.
- Final installer SHA-256: `0C69C95EA86CCA13C89EB5AA511ADC026DAB9643437CD88EFA18DFC323444599`.
- Final installation method: normal silent NSIS upgrade (`/S`), exit code 0; no force.
- Installed app: `C:\Users\codex-agent\AppData\Local\Niners War Room — Redraft\nwr-redraft-war-room.exe`, product version `1.0.3`.
- Installed sidecar SHA-256 matches the final built receipt: `E1E9EB05920DE2CC5D3F4B8A9BF3F5384EFAA21A3F0B65DCE50F00F25E39304D`.
- Post-install owner-state manifest: 24 files, SHA-256 `59F977866B777F4FE345E9E1B4BDAB62B01B1D040A2F015443448D773CD34C18`, unchanged from baseline.
