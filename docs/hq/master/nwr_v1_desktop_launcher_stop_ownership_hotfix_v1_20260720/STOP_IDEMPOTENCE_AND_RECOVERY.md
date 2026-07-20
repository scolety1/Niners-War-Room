# Stop idempotence and recovery

Concurrent duplicate Stop uses an exclusive identity-bearing guard; a second concurrent command fails closed without mutation. Sequential Stop returns `NOT_RUNNING` after completed finalization. Retained `RECOVERY_REQUIRED` can be resumed after launcher, Streamlit, browser, or listener partial exit.

The delayed proof returned exit 7 with durable `RECOVERY_REQUIRED`, healthy listener PID 30576, and Streamlit PID 23736. Status exposed the retained state. The subsequent exact Stop command exited 0 and cleared process, listener, ownership, and registrations.
