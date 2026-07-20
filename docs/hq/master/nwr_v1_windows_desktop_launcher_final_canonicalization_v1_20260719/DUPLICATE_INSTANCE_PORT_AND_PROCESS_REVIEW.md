# Duplicate instance, port, and process review

Port is deterministic `8520` on loopback. Health and verified ownership are both required for reuse. A stale lock plus occupied port fails closed; unrelated occupants are neither reused nor killed. Lock acquisition contains identity before returning. Stop and browser cleanup require recorded identity matches and target only owned trees. Live smoke ended with no listener and no launcher-owned process.
