# Launcher architecture

`scripts/nwr_desktop.py` is the repository entry point; `src/launcher/windows_desktop.py` owns configuration, validation, migration, junctions, snapshots, browser launch, lock/stop protocol, diagnostics, and the accepted lifecycle calls.

Startup verifies the accepted RC is an ancestor and its exact tree exists, Python/Streamlit are supported, the deterministic port is free, migration/junctions are safe, and current state validates. An exclusive JSON lock records launcher PID, child PID, runtime, repository, port, and accepted base. A duplicate opens the existing healthy instance without spawning Streamlit. An unrelated listener is never killed or reused.

Stop writes a request only after a live launcher ownership record is verified. The owning supervisor sends the accepted graceful signal, performs bounded escalation only through the accepted helper, verifies port release/fatal markers, snapshots changed valid state, and removes lock/request files.
