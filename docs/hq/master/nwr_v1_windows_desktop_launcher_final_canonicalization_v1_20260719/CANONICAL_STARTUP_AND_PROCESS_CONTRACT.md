# Canonical startup and process contract

Startup is `pythonw.exe "C:\NWR\Niners-War-Room-V1\scripts\nwr_desktop.py" start`. Diagnostics use matching `python.exe`. The launcher binds only `127.0.0.1:8520`, waits for HTTP readiness, reuses only a healthy verified NWR instance, and fails closed on an unrelated listener.

PID/lock records include process identity. Stop targets only verified launcher-owned processes, requests graceful shutdown, applies bounded Windows escalation, and proves listener release. It never performs broad Python, Chrome, or Edge termination. Ordinary launch uses `pythonw.exe`; diagnostics remain visible through status and logs.
