# Desktop shortcut installation

The tested installer is `scripts\Install Niners War Room Shortcut.ps1`. It resolves the Desktop known folder with .NET, requires exactly one Explorer owner matching the installer identity, requires a clean committed launcher worktree descending from accepted RC1, resolves `pythonw.exe`, creates `Niners War Room.lnk`, and reads it back to verify target and working directory.

Disposable result: created and removed successfully. Target was `C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\pythonw.exe`; arguments were the stable worktree `scripts\nwr_desktop.py start`; working directory was the stable launcher worktree. Install refuses to overwrite, and uninstall refuses to remove, a same-named shortcut unless its exact target, arguments, working directory, description, supported runtime, and (outside the disposable override) Explorer identity match this launcher. The icon is the local Windows `shell32.dll,13` resource because no repository NWR icon exists. No real desktop shortcut was created.

After the existing persistence blocker is resolved, run the installer once as the interactive Explorer user.
