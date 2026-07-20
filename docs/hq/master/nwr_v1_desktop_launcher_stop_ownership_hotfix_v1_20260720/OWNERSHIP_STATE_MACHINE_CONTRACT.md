# Ownership state-machine contract

`RUNNING` means the launcher, Streamlit tree, listener, and browser registrations have durable identity. Stop atomically advances to `STOP_REQUESTED`, revalidates identity, then advances to `STOPPING`. Incomplete bounded cleanup advances to `RECOVERY_REQUIRED` with remaining-resource evidence. Complete absence advances to `STOPPED`, writes `last_stop.json`, removes pending request/guard metadata, and only then removes the ownership record.

Status never maps `STOP_REQUESTED`, `STOPPING`, `RECOVERY_REQUIRED`, or retained `STOPPED` to `NONE`. Corrupt or partial ownership is preserved as unverified evidence.
