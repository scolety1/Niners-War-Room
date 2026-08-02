# Rollback Plan

Before adoption, delete the implementation/adoption branches and worktrees. After adoption, revert the authorized hardening commits in reverse order. Never restore source data from this packet, alter LocalData, enable scheduled refresh, or touch the operational checkout.
