@echo off
title NWR -- Draft Upgrade Preview (work/nwr-draft-upgrade-hq-v1-20260903)
echo ============================================================
echo NWR -- DRAFT UPGRADE PREVIEW
echo Worktree: C:\Users\codex-agent\orca\workspaces\Niners-War-Room\draft-upgrade-hq
echo Branch:   work/nwr-draft-upgrade-hq-v1-20260903
echo This is a DEV build launch (tauri dev), not an installed release.
echo First launch compiles Rust and may take several minutes.
echo Data root is the SAME shared %%LOCALAPPDATA%%\com.ninerswarroom.redraft
echo store your other NWR shortcuts use. Use a NEW test profile in the
echo app -- do NOT open/pick inside the real KHA profile from here.
echo ============================================================
cd /d "C:\Users\codex-agent\orca\workspaces\Niners-War-Room\draft-upgrade-hq\desktop"
echo Verifying/building the nwr-desktop-api sidecar (skips rebuild if current)...
call npm run sidecar:build
if errorlevel 1 (
  echo Sidecar build failed -- see output above. Not launching Tauri.
  pause
  exit /b 1
)
call npm run tauri:redraft
echo.
echo Draft Upgrade Preview process exited. Press any key to close this window.
pause >nul
