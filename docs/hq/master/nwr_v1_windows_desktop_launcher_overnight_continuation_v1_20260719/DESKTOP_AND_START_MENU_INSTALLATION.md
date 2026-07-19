# Desktop and Start Menu installation

Installation state: none. `C:\Users\codex-agent\Desktop\Niners War Room.lnk` and the sandbox Programs-folder candidate were absent, but the sandbox Known Folders are not accepted as the actual interactive user's folders. `GetOwner` access for Explorer was denied and zero owners were resolvable.

The tested installer requires a clean committed worktree, accepted ancestor/tree, supported `pythonw.exe`, one Explorer owner exactly matching the installer identity, and collision-safe shortcut identity. It refuses overwrite or uninstall of a foreign same-named shortcut. Start Menu creation is not implemented and was not added because it is only optional when already safely supported. Taskbar pins are untouched.

After both blockers are resolved and canonical adoption creates `C:\NWR\Niners-War-Room-V1`, run its `scripts\Install Niners War Room Shortcut.ps1` interactively. Inspect target, arguments, working directory, description, and icon afterward.
