# Process, port, and lock review

Port 8520 is deterministic. A healthy existing instance is accepted only with a valid launcher-version lock, live launcher PID, and healthy endpoint. A listener without that proof is unrelated and is never killed or reused.

The supervisor directly owns the Streamlit process tree created by the accepted helper. The exclusive lock is populated and flushed with a nonce plus launcher executable/creation identity before acquisition returns; `STARTING`, `RUNNING`, and `MAINTENANCE` states fail closed against concurrent operations. Healthy reuse additionally requires exact repository/commit/port identity, helper and listener executable/creation identities, the recorded listener PID to own the actual socket, and that listener to be a descendant of the launched helper. Stop targets the verified supervisor through a file request; it never enumerates or kills generic Python/Chrome/Edge processes. Windows identity uses `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)`, process image, creation time, and parent-process ancestry. Stale locks are removed only when the owner identity is no longer valid and the port is free.

The final real synthetic cycle reported `VERIFIED_RUNNING`, health 200, duplicate exit 0, graceful stop, and no listener afterward. The exact test junctions and synthetic profile were then removed; supported user-state roots were untouched.

Observed clean cycles: Streamlit exit 0, `forced_cleanup=false`, no fatal markers, port released, supervisor exit 0. Abrupt termination recovery preserved state and cleared the stale lock on the next valid start.
