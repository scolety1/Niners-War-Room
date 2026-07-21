# Desktop and Start Menu installation

The canonical installer resolves the interactive user's Desktop, Programs, and LocalAppData Known Folders, requires an exact clean stable checkout at canonical HQ, and validates every saved `.lnk`.

Primary app shortcuts use `C:\NWR\Niners-War-Room-V1\assets\branding\nwr_desktop_icon.ico,0`. Command shortcuts continue to use `%SystemRoot%\System32\shell32.dll,13` unless an existing exact-owned command shortcut already has a meaningful custom icon, which is preserved.

Disposable integration coverage proves fresh creation, idempotent update, stale app-icon replacement, wrong-target rejection, unrelated same-name protection, missing-icon rejection, redirected Desktop roots, spaces, non-ASCII paths, uninstall data preservation, and reinstall icon restoration.

Post-push installation is restricted to the two exact identity-matching primary shortcuts. A bounded shell association notification may be requested. Global icon-cache deletion, Explorer restart, sign-out, reboot, administrator access, and unrelated shortcut deletion are prohibited.
