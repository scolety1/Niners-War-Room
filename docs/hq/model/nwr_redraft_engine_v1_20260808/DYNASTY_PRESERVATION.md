# Dynasty Preservation

The implementation is additive. It does not modify Finished V1 ranking artifacts, Outcome V3,
Rookie Review, Unified Research Preview, Trading Lab policy, active-pack data, scheduled refresh,
or Personal Workspace persistence. Redraft writes are confined to the independent ignored redraft
store and occur only after explicit controls. Page-open reads do not create directories or files.
