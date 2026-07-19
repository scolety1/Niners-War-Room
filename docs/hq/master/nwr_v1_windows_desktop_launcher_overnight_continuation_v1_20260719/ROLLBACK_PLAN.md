# Rollback plan

No remote or installed-machine rollback is currently required because nothing was pushed or installed. Local source rollback, if explicitly authorized, is to stop NWR, preserve external state, and return from correction commit `4c6fd44358d03b38565e71afc4c23c8abeb2b92e` to implementation commit `f227e0bdb3a6557a7c59437baa969c7c28572b48`; do not use destructive reset while user work may exist.

For a future installed version, run the identity-safe uninstaller, stop the verified launcher, preserve all external roots, and replace only the clean runtime checkout. Data rollback uses an explicit validated snapshot dry-run and exact confirmation. Never delete the legacy invalid receipt or choose between divergent states automatically.
