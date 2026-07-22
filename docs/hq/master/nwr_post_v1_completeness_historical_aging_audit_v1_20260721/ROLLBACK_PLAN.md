# Rollback plan

Website rollback is one local revert of
c0b3a136d3fdbb247cd702cbc7b7300676bda859. It restores the Draft Cockpit root
wrapper and prior default title while leaving /draft-cockpit itself unchanged.

Documentation rollback is removal or revert of the second local audit commit.
Neither rollback requires data migration, provider refresh, ranking rebuild,
shortcut reinstall, LocalData restoration, or user CSV handling.

After any rollback, rerun focused root tests, all route tests, exact 240-row
ranking proof, Hermetic, LocalData, persistence hashes, launcher Start and Stop,
port cleanup, and protected/frozen checks. Do not push without Master HQ review.
