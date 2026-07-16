# Privileged Policy Isolation Contract

Before a repository-writing worker starts, the supervisor copies the policy, guardrail, security helper, and build script into a unique temporary envelope outside the repository. SHA-256 digests are recorded and read-only file handles are held. Relevant Git configuration files are also digested and locked.

The frozen policy owns allowed/blocked/protected paths, blocked terms, executable identity, argument array, working directory, maximum file count, repository binding, parent, branch, remote, commit authority, and push authority. `PROFILE.json` can only supply values before the freeze and must contain the one approved legacy static-check string. Its text is never executed.

Candidate edits to `PROFILE.json`, security automation, gate selection, bootstrap, no-skip plugin, or tier manifest are protected and rejected by the supervisor. Both `commitAllowed` and `pushAllowed` are frozen to `false`.
