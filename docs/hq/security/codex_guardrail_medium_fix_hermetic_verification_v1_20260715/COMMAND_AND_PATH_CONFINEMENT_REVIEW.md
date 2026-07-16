# Command and Path Confinement Review

- `Invoke-Expression` and its aliases are absent from the supervisor.
- The build uses resolved `powershell.exe` plus a structured argument array.
- Exit status is captured and handled explicitly.
- The requested working directory must exist beneath the approved repository root on the same drive.
- `..` traversal, UNC roots, alternate drives, arbitrary absolute roots, missing directories, and detectable symlink/junction traversal reject.
- The directory is frozen in the policy and rechecked through the trusted-envelope digest.
- Hermetic dependency resolution uses `uv run --offline --no-project` with a fixed package list. No project lock or metadata file is generated.

Controls 09-12 prove inert repository command text, literal structured arguments, and path rejection. No network-capable command exists in the bootstrap.
