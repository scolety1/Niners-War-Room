# Browser registration lifecycle

Chrome/Edge registration now carries full identity, repository, data root, profile, and run ID. Browser descendants are captured and atomically stored before signaling. A dead root does not clear registration while a verified descendant remains. Malformed, reused, or unrelated identity is preserved without targeting.

Three live app-mode cycles stopped all registered Chrome trees. Intermediate waits are reported as recovered only after final verified absence.
