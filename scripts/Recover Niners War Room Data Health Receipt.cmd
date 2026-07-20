@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Recover Niners War Room Data Health Receipt.ps1"
set "NWR_RECOVERY_EXIT=%ERRORLEVEL%"
echo.
if "%NWR_RECOVERY_EXIT%"=="0" (
  echo Niners War Room Data Health recovery finished.
) else (
  echo Niners War Room Data Health recovery did not finish. No success receipt was fabricated.
)
pause
exit /b %NWR_RECOVERY_EXIT%
