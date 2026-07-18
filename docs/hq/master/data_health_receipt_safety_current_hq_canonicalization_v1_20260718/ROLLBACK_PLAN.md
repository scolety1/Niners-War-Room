# Rollback Plan

If rollback is required after adoption, use ordinary non-rewriting Git history:

1. Revert the documentation-only canonicalization commit at the final branch tip.
2. Revert implementation commit fdc57ab19cc619fb95b82dc4159bb32d359d8d67.
3. Run the same strict Hermetic gate and capture the LocalData tier independently.
4. Push the two revert commits normally after verifying the canonical remote has not advanced unexpectedly.

Do not reset, force push, rewrite either historical source commit, adopt rejected review commit 559985ec2af0433578a98b7d42f098fee3926fc9, or modify the five user-owned DynastyProcess CSVs. Local ignored receipt files may be retained for diagnosis; removal is not required to roll back repository code.
