# Windows process lifecycle final revalidation

Result: `BOUNDED_WINDOWS_PROCESS_LIFECYCLE_MITIGATION_VALIDATED_BY_REPEAT_RUNS`.

The exact committed candidate was exercised in three independent short-path clean worktrees. The runner used the supported direct Python launcher, an owned Windows process group, explicit browser teardown before shutdown, explicit Streamlit shutdown ordering, `CTRL_BREAK_EVENT`, strict process exit-code checks, fatal-marker checks, listener and port checks, child-process checks, and a second-start verification in every cycle.

All six starts succeeded. All six graceful shutdowns returned exit code 0. There was no forced cleanup, retained listener, retained Streamlit process, unexpected connection reset, or fatal marker. Port 8520 was released after every shutdown and absent at the final audit.

The logs did not contain `_PySemaphore_Wakeup`, `ReleaseSemaphore failed`, or `ERR_CONNECTION_RESET`. Nonzero unexpected exit codes were not suppressed; none occurred. Retained processes and listeners were not ignored; none remained.

This validates a bounded Windows process-lifecycle mitigation by repeat runs. It does not prove which external dependency owned or closed the historical CPython handle, and it does not claim that root cause was proven.
