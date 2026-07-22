# Rollback plan

The closeout is one documentation/operational commit after the adopted
canonicalization commit. Roll it back with a normal reviewed revert; never
force-push or rewrite work/hq-parallel-control.

Reverting removes the seven user guides, three research guides, 16 generated
screenshots, and this 23-file packet. It requires no production model, ranking,
or persistent-state restoration. The separately created manual backup remains
valid under normal retention.

After rollback, re-run Hermetic, LocalData, ranking identity, persistent
digests, shortcut target/icon, and launcher-owned Start/Stop checks.
