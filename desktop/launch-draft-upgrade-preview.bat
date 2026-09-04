@echo off
setlocal enabledelayedexpansion
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

set "REPO_ROOT=C:\Users\codex-agent\orca\workspaces\Niners-War-Room\draft-upgrade-hq"

REM --- Resolve the dev Python interpreter ------------------------------------
REM desktop\crates\nwr-desktop-runtime resolve_python() (debug build) checks,
REM in order: 1) NWR_DESKTOP_PYTHON  2) <repo_root>\.venv\Scripts\python.exe
REM 3) a raw PATH scan for python.exe.
REM
REM Step 3 is unreliable on this machine (the python.exe "App Execution
REM Alias" stub shadows the real interpreter on PATH) -- that produced the
REM original NWR_DESKTOP_RUNTIME_LAUNCH_FAILED: could not locate python.exe.
REM
REM Step 2 (a project-local .venv) was tried first and does create a working
REM interpreter (see README.md's documented `python -m venv .venv` setup,
REM still valid for local `pytest`/`ruff` work) -- but on this machine's
REM Python install (the newer "Python Install Manager" pythoncore-3.14-64
REM layout) a venv's Scripts\python.exe spawns a grandchild python.exe
REM rather than being the process that itself binds the API socket, which
REM fails the desktop runtime's own listener-ownership security check
REM ("API listener image does not match the launched backend"). That is a
REM real Windows/Python-install-specific incompatibility, not fixed by
REM retrying.
REM
REM So this launcher uses step 1 instead, exactly like this project's own
REM proven-working canonical Redraft dev launcher
REM (desktop\LAUNCH_KHA_HIGH_STAKES_DRAFT.bat in a sibling NWR worktree):
REM point NWR_DESKTOP_PYTHON at the real base interpreter directly, for
REM THIS dev launch only (a session-scoped environment variable, never
REM written into source or any committed config) -- discovered dynamically
REM via the Python Launcher (`py`) rather than hard-coded, so this script
REM stays portable across machines that have Python registered differently.
where py >nul 2>nul
if errorlevel 1 (
  echo.
  echo ERROR: the Python launcher ^(py.exe^) was not found on PATH.
  echo Install Python 3.12+ from python.org ^(the installer registers the
  echo py launcher automatically^), then re-run this shortcut.
  pause
  exit /b 1
)
for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)"') do set "NWR_DESKTOP_PYTHON=%%P"
if not exist "%NWR_DESKTOP_PYTHON%" (
  echo.
  echo ERROR: py -3 did not resolve to a real interpreter file.
  pause
  exit /b 1
)
echo Using Python interpreter: %NWR_DESKTOP_PYTHON%

echo Verifying required backend dependencies import cleanly...
"%NWR_DESKTOP_PYTHON%" -c "import nflreadpy, numpy, pandas, pydantic, streamlit" 2>nul
if errorlevel 1 (
  echo Dependencies missing on this interpreter -- installing NWR's declared
  echo dependencies ^(pyproject.toml: python -m pip install -e . pytest ruff,
  echo per README.md's "Runtime and installation" section^)...
  "%NWR_DESKTOP_PYTHON%" -m pip install -e "%REPO_ROOT%" pytest ruff
  if errorlevel 1 (
    echo Dependency install failed -- see output above. Not launching Tauri.
    echo Refusing to launch against an interpreter missing required deps.
    pause
    exit /b 1
  )
  "%NWR_DESKTOP_PYTHON%" -c "import nflreadpy, numpy, pandas, pydantic, streamlit" 2>nul
  if errorlevel 1 (
    echo Dependencies still missing after install -- not launching Tauri.
    pause
    exit /b 1
  )
)
echo Backend dependencies OK.

REM Dev-mode Tauri (tauri dev) spawns the real Python source directly via
REM resolve_python()/resolve_api_script() above -- it never touches the
REM frozen PyInstaller sidecar (see resolve_backend_program()'s
REM #[cfg(not(debug_assertions))] branch, which is compiled out of a debug
REM build entirely). Building the sidecar first is unnecessary for this dev
REM preview launch and is skipped here to match the canonical Redraft dev
REM launcher pattern used elsewhere in this project.

cd /d "%REPO_ROOT%\desktop"
call npm run tauri:redraft
echo.
echo Draft Upgrade Preview process exited. Press any key to close this window.
pause >nul
