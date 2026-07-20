# Shortcut and installer review

Production installation is accepted only from the fixed standalone stable checkout at exact clean HQ. It proves interactive identity and Known Folders, shows resolved user/destinations/runtime/commit, and requires exact typed confirmation. Collision preflight validates target, arguments, working directory, description, and icon. Exact existing links are returned without `Save()`, preserving bytes; only absent paths are written and deleted on transaction failure.

The package creates Desktop `Niners War Room.lnk` and a Start Menu `Niners War Room` folder containing launch, stop, status, backup, restore dry-run, recovery, installer, and uninstaller entries. Icon is `%SystemRoot%\System32\shell32.dll,13`. Uninstaller applies the same exact-HQ, clean-tree, identity, Known Folder, and ownership gates and preserves data/backups.
