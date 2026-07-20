# Rollback and emergency Stop plan

Rollback is a normal two-commit revert in reverse order: revert the documentation-only canonicalization commit, then implementation commit `d8286da34eab8bedf5d2f3f3b0176d29a696ed66`. Never force push and never delete LocalData.

Emergency Stop must load retained ownership, verify PID/creation/executable/command line/repository/data root/listener/run ID, terminate only that exact tree, recheck browser descendants and port, write the final receipt, and only then remove ownership. Identity conflict requires review; broad Python/Chrome/Edge termination is prohibited.
