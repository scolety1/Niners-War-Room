# Desktop launcher and shortcut status

The installed shortcut is C:\Users\codex-agent\Desktop\Niners War Room.lnk.
It targets Windows PowerShell with the stable
scripts\NWR Desktop Commands.ps1 start command, uses the stable checkout as its
working directory, and points to the existing NWR desktop icon.

Shortcut launches reached HEALTHY and VERIFIED_RUNNING. In this host, an
external app-browser root exited after startup during one observation. The
launcher shut Streamlit down and failed closed when a recorded launcher PID had
been reused; no unrelated process was targeted. A bounded second canonical
Stop finalized the owned browser tree and released port 8520.

The supported no-browser launcher mode remained healthy for the full UI
walkthrough and stopped cleanly on the first canonical Stop. Launcher
regressions passed. The final post-push shortcut launch/Stop is recorded in the
final operational readback.
