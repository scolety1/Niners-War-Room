# Browser app mode and profile review

The launcher uses an isolated profile at `%LOCALAPPDATA%\NinersWarRoom\browser-profile`, prefers Chrome app mode, then Edge app mode, then the default browser. Browser PID registration is atomic and identity-validated; registration or identity failure reaps only the directly created process. Malformed registrations are removed without targeting a process. A real interactive GUI session remains pending because Explorer ownership is unresolved.
