# Data Health recovery status

Real latest receipt is still `CORRUPT`, 40,881 bytes, SHA-256 `adefb7b4b51e824ddae19db2ddce9f424e2a5188bc89322a162424f5169e78da`. No valid latest, canonical backup, or top-level LKG archive was found. Real bytes were not changed.

Status: `READY_FOR_ONE_CLICK_DATA_HEALTH_RECOVERY`. Run the stable checkout's `scripts\Recover Niners War Room Data Health Receipt.cmd` as the real logged-in user and type `QUARANTINE_CORRUPT_RECEIPT`. It creates/verifies rollback backup, uses canonical quarantine, performs no refresh, and fabricates no success.
