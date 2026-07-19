# Windows Streamlit failure reproduction

Environment: Windows, Python 3.14.6, Streamlit 1.59.2, short runtime environment `C:\NWR\rtv`, detached clean RC checkout at `c380956dcab863dd7f921ec237506c08f46990b8`.

Three bounded unmodified-RC attempts used direct browser/CDP navigation at 375, 768, and 1440 widths. All three deterministically reproduced `/draft-cockpit-root` falling to `/` with an active Page Not Found dialog.

Attempt 1 used ordinary navigation and console shutdown. Attempt 2 captured `powershell -> uv.exe -> streamlit.exe -> python.exe -> listener python.exe` and intentionally terminated only the listener child as a bounded negative probe. Attempt 3 used ordinary navigation, browser close, and console shutdown. None emitted `_PySemaphore_Wakeup`, `ReleaseSemaphore failed`, or an unexpected browser reset. Listener/process cleanup was verified after each bounded attempt.

The rejected review remains authoritative evidence that the exact fatal occurred there. This lane does not relabel an intermittent failure as environmental. It bounds the failure at teardown/interpreter finalization and corrects the controllable ownership path.

During the corrected full 180-case matrix, an ad-hoc console shutdown released port 8520 but retained the owned interpreter pair until explicit exact-PID cleanup. No semaphore fatal was emitted. That observation is why ad-hoc console ownership is not the accepted test path.
