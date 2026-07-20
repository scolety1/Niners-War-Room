# Process identity revalidation

Every target is checked using PID, creation time, executable, full command line, parent relationship, repository, data root, listener ownership, and launcher run ID. Verified descendants are captured before signaling. Identity is checked again immediately before forced escalation.

PID reuse, changed listeners, partial identity, malformed browser registration, and unrelated Chrome/Edge identity produce preserved conflicts. No PID-only ownership is accepted and no unrelated process is targeted.
