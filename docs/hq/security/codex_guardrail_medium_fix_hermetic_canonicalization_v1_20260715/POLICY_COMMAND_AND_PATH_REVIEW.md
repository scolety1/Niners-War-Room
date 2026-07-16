# Policy, Command, and Path Review

Privileged controls are copied outside the worker tree before execution, SHA-256 authenticated, and held by read-only handles. Git configuration is included in the trusted envelope. Profile changes cannot redefine allowed/blocked/protected paths, executable identity, structured arguments, working directory, Git binding, commit authority, or push authority.

The supervisor admits only the exact legacy static-check string, never evaluates it, and invokes resolved `powershell.exe` with a fixed argument array. `Invoke-Expression` and `iex` are absent.

Working directories must be existing children of the approved repository root on the same drive. Traversal, UNC, arbitrary absolute, alternate-drive, and detectable junction/symlink paths reject. The directory and executable identity are frozen before the worker starts.

Review result: all policy, command, path, and alternate-bypass criteria pass.
