# Rollback and recovery plan

## Before HQ adoption

Do not delete or rewrite the candidate. To decline it, leave `work/nwr-v1-release-readiness-v1-20260718` unadopted and continue from canonical HQ `7a3d01a5fdd95f4a71d49ced7ff00b334434aa73`.

## After adoption

Create a normal revert commit for the single release-candidate commit. Do not reset a shared branch, force-push, delete LocalData, or restore the five primary-worktree CSVs. Verify the resulting tree against the canonical base tree `b4ab40e584c7c1d39d00f93ee8e5725dc22aafdf`, then rerun Hermetic, LocalData separation, focused security, Data Health passive reads, route smoke, protected proof, and primary hashes.

## Operational recovery

If startup fails, stop the local Streamlit process, confirm no test port listener remains, return to the canonical base or revert commit, bootstrap the deterministic Hermetic pack, and rerun the canonical gate. Missing private data must remain unavailable rather than be copied from another checkout.

## Acceptance stop conditions

Stop adoption on remote HQ advance with unresolved protected conflicts, Hermetic nonzero, LocalData result other than pass-with-valid-pack or exact missing-pack exit 4, any security/trust/source/identity regression, protected diff, primary hash drift, or a second correction cycle.
