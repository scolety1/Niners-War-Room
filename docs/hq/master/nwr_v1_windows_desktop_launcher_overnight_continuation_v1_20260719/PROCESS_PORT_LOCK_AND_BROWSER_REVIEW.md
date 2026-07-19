# Process, port, lock, and browser review

Port 8520 is deterministic and loopback-only. Ownership requires repository/commit/port identity, launcher/helper/listener PID plus executable and creation time, listener socket ownership, descendant ancestry, and healthy Streamlit response. The exclusive populated lock has `STARTING`, `RUNNING`, and `MAINTENANCE` states; unrelated occupied ports fail closed. Stop signals only the verified supervisor, which uses the accepted graceful Streamlit lifecycle before bounded escalation.

Chrome/Edge launches are registered with PID, executable, creation time, isolated profile, repository, and an installed approved browser path. Explicit stop reconciles all registrations and targets only exact verified PID trees; malformed or PID-reused records are removed without targeting. Registration failures synchronously terminate/wait/kill/wait the directly created process. Default-browser fallback is not treated as launcher-owned.

The final real no-browser cycle left no launcher, Streamlit listener, lock, or port. Chrome and Edge commands and cleanup logic are tested; a real GUI browser process was not launched because installation identity is unresolved.
