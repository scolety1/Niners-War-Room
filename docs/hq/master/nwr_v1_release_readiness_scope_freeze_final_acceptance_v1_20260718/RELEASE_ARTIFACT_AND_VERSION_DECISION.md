# Release artifact and version decision

- Recommended identifier: **NWR V1 Release Candidate 1**
- Repository-native product version remains `0.1.0`; this lane does not invent or edit a conflicting semantic-version convention.
- Result form: local release candidate, not final public V1.
- Canonical base: `7a3d01a5fdd95f4a71d49ced7ff00b334434aa73`
- Canonical base tree: `b4ab40e584c7c1d39d00f93ee8e5725dc22aafdf`
- Candidate branch: `work/nwr-v1-release-readiness-v1-20260718`
- Commit message: `chore: prepare NWR V1 release candidate`
- Tag/public release: not created.
- Push: not performed.

The manifest includes the 24-file acceptance packet, the bounded correction diff, included/excluded capability inventory, route/workflow inventory, validation evidence, protected proof, primary preservation, and rollback.

Rollback target is the exact canonical base. Final human acceptance must reverify remote ancestry, read the full candidate diff and this packet, confirm post-commit Hermetic 2,614/exit 0 and LocalData exit 4, confirm automation is disabled, and decide whether to adopt the commit into Master HQ.
