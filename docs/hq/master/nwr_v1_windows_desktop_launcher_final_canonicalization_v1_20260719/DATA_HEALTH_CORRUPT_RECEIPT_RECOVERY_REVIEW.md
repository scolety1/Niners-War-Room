# Data Health corrupt receipt recovery review

Canonical read-only inspection used the accepted receipt API. Root: `C:\NWR\Niners-War-Room\local_exports\refresh_data`. Latest: `latest_refresh_status.json`, 40,881 bytes, SHA-256 `adefb7b4b51e824ddae19db2ddce9f424e2a5188bc89322a162424f5169e78da`. Load status: `CORRUPT`; category: legacy/missing current closed-schema integrity and lifecycle fields. Canonical backup: `MISSING`. Five top-level receipt candidates were also invalid legacy receipts; no valid matching LKG was found. Receipt contents were not copied.

Real bytes remain untouched. The explicit recovery command accepts only corrupt/oversized latest state, blocks any valid latest/backup/archive LKG, backs up the complete service-owned receipt store (latest, canonical backup, numeric receipt archives, quarantine JSON) outside Git, writes and validates path/size/SHA-256 manifest, proves exact restore with the production restore function, calls the existing canonical quarantine API, and rolls back exact scope on failure. Raw/provider caches are excluded and no refresh or synthetic success is created.

Result: `READY_FOR_ONE_CLICK_DATA_HEALTH_RECOVERY`. The real user must run `scripts\Recover Niners War Room Data Health Receipt.cmd` from the stable checkout and type `QUARANTINE_CORRUPT_RECEIPT`.
