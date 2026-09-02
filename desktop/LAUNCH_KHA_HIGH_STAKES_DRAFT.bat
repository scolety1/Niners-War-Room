@echo off
REM NWR -- KHA HIGH STAKES DRAFT launcher.
REM
REM Runs the Redraft Desktop app in Tauri debug/dev mode, which spawns the
REM real Python service directly (src\services\redraft_engine_v1_service.py
REM / redraft_draft_room_v1_service.py via scripts\run_nwr_desktop_api.py) --
REM see desktop\crates\nwr-desktop-runtime\src\lib.rs resolve_backend_program()
REM under #[cfg(debug_assertions)]. This intentionally bypasses the frozen
REM PyInstaller sidecar, which could not be produced in tonight's build
REM environment (see the readiness report's Installed app section).
cd /d "%~dp0"
REM Windows' python.exe App Execution Alias is not reliably found by a raw
REM PATH scan from a spawned child process -- point at a real interpreter
REM directly so the desktop runtime can find it. Adjust this path if python
REM is installed elsewhere on this machine.
set "NWR_DESKTOP_PYTHON=C:\Users\codex-agent\AppData\Local\Python\pythoncore-3.14-64\python.exe"
npm run tauri:redraft
