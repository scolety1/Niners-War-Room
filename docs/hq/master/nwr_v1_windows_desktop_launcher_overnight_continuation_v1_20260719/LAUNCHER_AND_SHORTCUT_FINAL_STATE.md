# Launcher and shortcut final state

Launcher source is committed locally on `work/nwr-v1-desktop-launcher-v1-20260719`; ordinary launch uses `pythonw.exe` and exposes no terminal. Exact Streamlit child command is `C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\python.exe -m streamlit run app/main.py --server.address 127.0.0.1 --server.port 8520 --server.headless true --browser.gatherUsageStats false`.

Candidate shortcut contract: target `C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\pythonw.exe`; arguments `"<stable-checkout>\scripts\nwr_desktop.py" start`; working directory `<stable-checkout>`; icon `C:\Windows\System32\shell32.dll,13`. Chrome app mode is preferred, Edge second, default browser last. Chrome and Edge use an isolated `%LOCALAPPDATA%\NinersWarRoom\browser-profile`.

No Desktop or Start Menu shortcut exists. Sandbox Known Folders resolved to `C:\Users\codex-agent\Desktop` and the corresponding Programs folder, but Explorer ownership could not be queried; those paths are not accepted as proof of the actual interactive user.
