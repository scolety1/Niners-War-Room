# Delayed-shutdown recovery proof

An isolated Streamlit cycle deliberately survived the first wait and disabled first-command escalation. First Stop exited 7, wrote `RECOVERY_REQUIRED`, retained ownership, and recorded launcher 19160, Streamlit 23736, listener 30576, and verified descendants. Status returned `HEALTHY` and `process_ownership: RECOVERY_REQUIRED`, never `NONE`.

The subsequent exact command `python scripts/nwr_desktop.py stop` exited 0. Ownership was absent, port 8520 was free, and browser registrations were zero.
