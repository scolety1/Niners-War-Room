# Process lifecycle root cause and fix

The fatal signature is a CPython Windows parking-lot semaphore wakeup failing because `ReleaseSemaphore` received an invalid handle during shutdown/finalization. The NWR-specific evidence does not prove which external dependency closed that handle; the fatal was intermittent and did not reproduce in three controlled RC attempts.

The actionable NWR cause was insufficient teardown ownership: a shell/uv/Streamlit/interpreter chain and forced or console-level termination could race child-resource cleanup. A reused browser tab across a server restart could also retain stale Page Not Found UI even after corrected content rendered.

Correction boundary:

1. Launch the exact Python runtime with `-m streamlit`, `shell=False`.
2. Create a new Windows process group.
3. Refuse an occupied test port.
4. Expose explicit readiness and shutdown-trigger files for browser orchestration.
5. Close/finalize the browser before shutdown.
6. Send `CTRL_BREAK_EVENT` and wait for a bounded clean exit.
7. Treat timeout termination, nonzero exit, retained listener, or fatal marker as failure.
8. Start again on the same port to prove cleanup.

The application does not suppress stderr, intercept the fatal, or accept connection reset. No dependency upgrade or platform rewrite was needed.
