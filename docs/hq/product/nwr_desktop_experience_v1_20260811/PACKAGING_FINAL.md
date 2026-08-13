# Packaging Final

Date: 2026-08-13

## Definitive artifacts

| Product | Format | SHA-256 |
|---|---|---|
| Dynasty | MSI | `BE8621573E6CD896A57023EFC0EC151C4E244865EBED7901E09C9A107678B139` |
| Redraft | MSI | `6810BF9E0AAE525813A8AE45F92C6BF73E2D46DEE259A582ABB3B4955FD5C331` |
| Dynasty | NSIS EXE | `046B86F36CC87313B2A53A54F6534EC13CCB972C53AD6249AF93F2289304537D` |
| Redraft | NSIS EXE | `A7A727D2C07CE8341D156C2040C2C3069266EB211DE8CFC173E7FDA2A50939A6` |
| Shared frozen API sidecar | EXE | `FF06906C1138FBCD64EF48525560703F3C3FC67A1D07F2E6F743472DD7891BCF` |

Both definitive MSI administrative extractions returned exit code 0. Both extracted sidecars match the build receipt exactly.

## Acceptance

- Exact mode-specific resource allowlists passed for both extracted MSIs.
- No `sample_data`, broad templates/data packs, Python source, caches, owner workspace, Redraft saved state, `.env`, or cross-mode evidence is packaged.
- Distinct executable names, product names, Tauri identifiers, taskbar/app icons, installer icons, MSI UpgradeCodes, LocalAppData roots, and shortcuts are retained.
- Each app launches its frozen sidecar from its own extracted payload, uses a random ephemeral loopback port, verifies startup HMAC and authenticated health, and reports `windows-job-object` containment.
- Simultaneous operation uses distinct ports. Duplicate launches exit after focusing the existing mode. Shutdown and forced-host tests leave no package process/listener.
- True Redraft first run creates the governed projection seed and zero league profiles; the owner is prompted to create a profile.
- A final fresh extraction launched one host plus its frozen sidecar for each mode; exact-host forced close exercised Job Object containment and left zero package processes.

## Paths

- Dynasty MSI: `desktop/target/release/bundle/msi/Niners War Room — Dynasty_1.0.0_x64_en-US.msi`
- Redraft MSI: `desktop/target/release/bundle/msi/Niners War Room — Redraft_1.0.0_x64_en-US.msi`
- Dynasty NSIS: `desktop/target/release/bundle/nsis/Niners War Room — Dynasty_1.0.0_x64-setup.exe`
- Redraft NSIS: `desktop/target/release/bundle/nsis/Niners War Room — Redraft_1.0.0_x64-setup.exe`
- Definitive extracted audit: `C:/Users/codex-agent/Documents/Niners War Room/desktop-v2-final-audit-final2`

These artifacts are local review candidates. They were not installed system-wide, signed, published, pushed, or adopted by canonical HQ.
