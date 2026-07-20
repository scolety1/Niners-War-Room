# Interactive user and Known Folder review

The Codex execution identity is not sufficient proof of the real Explorer user. Production installer, recovery, and uninstaller require exactly one same-session `explorer.exe` owner equal to the current Windows identity. Desktop, Programs, and LocalAppData are resolved through Windows Known Folder APIs at execution time.

Disposable testing is allowed only beneath the fixed sibling `.codex-known-folder-tests` boundary with an exact marker and no reparse point. No real Desktop or Start Menu shortcut was installed during repository review.
