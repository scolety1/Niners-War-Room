# Windows process lifecycle mitigation revalidation

Classification revision testing preserved and revalidated the direct Python launcher, owned Windows process group, browser-before-shutdown ordering, `CTRL_BREAK_EVENT`, and strict process-exit, listener, port, and fatal-marker checks.

Result: `BOUNDED_WINDOWS_PROCESS_LIFECYCLE_MITIGATION_VALIDATED_BY_REPEAT_RUNS`.

Three consecutive pre-commit clean-fixture cycles passed. Their primary route profiles were 180/180, 34/34, and 34/34; each cycle also completed a second cold start and graceful shutdown. All six shutdowns exited 0 without forced termination and released port 8520. Final checks found zero retained listeners and zero retained runtime Python processes.

Across 18 captured logs, `_PySemaphore_Wakeup`, `ReleaseSemaphore failed`, `ERR_CONNECTION_RESET`, `Page Not Found`, and `Uncaught app exception` each occurred zero times. Browser inspection found no visible traceback and no console errors.

This evidence validates bounded mitigation by repeat runs. It does not claim that the external CPython handle owner was proven.
