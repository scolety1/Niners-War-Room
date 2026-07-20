# Data and backup no-change proof

All destructive tests used isolated `C:\NWR\hfxdata` or `C:\NWR\hfxdelay`. The real `%LOCALAPPDATA%\NinersWarRoom` inventory was hashed before and after: all 13 non-browser-profile files matched exactly, including backup payload, launcher logs, Data Health recovery content, and `run\last_backup.json`.

No retention, schema, restore, migration, draft-state, Data Health, or Trading Lab persistence behavior changed.
