@echo off
REM Saves a timestamped, read-only copy of the REAL 2026 KHA High Stakes
REM League profile + draft board + ADP/provider state, for manual recovery.
REM No watcher, no locking redesign, no background writer -- run this
REM yourself whenever you want a safety copy (e.g. right before the draft
REM starts, and again if you want a mid-draft snapshot).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\save-kha-draft-checkpoint.ps1" %*
pause
