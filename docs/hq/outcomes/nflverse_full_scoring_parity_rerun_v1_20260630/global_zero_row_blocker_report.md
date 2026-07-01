# Global Zero Row Blocker Report

Global scoring parity remains blocked because compact V1 does not emit explicit zero rows for all components and all eligible player-week/component combinations.

Observed zero rows are allowed only when an observed source row contains an explicit numeric zero for the component being emitted. Missing player-week rows are not converted to zero. This preserves the missingness rule and prevents false misses.

Current status: `global_scoring_ready=false` for every matrix row.
