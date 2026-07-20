# Shutdown sequence and finalization

Stop loads scope-bound ownership, takes an exact Stop guard, writes `STOP_REQUESTED`, revalidates, captures descendants, writes `STOPPING`, requests graceful browser and Streamlit shutdown, and polls processes, listener, registrations, and port. If resources remain, it writes `RECOVERY_REQUIRED` before bounded exact-tree escalation. Final absence is rechecked before `STOPPED`, the atomic receipt, request cleanup, guard release, and ownership deletion.

Atomic-write or deletion failure is nonzero and retains recoverable evidence. No ownership deletion exists in the launcher's unconditional `finally` path.
