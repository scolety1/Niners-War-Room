# Full packet build contract

Authoritative command:

```powershell
python scripts/build_exact_model_v4_replay_accuracy_audit_v1.py `
  --source-commit 0929ce6ec058a698efeee10fe5770f56047bab21 `
  --repo-root <EXACT_CLEAN_CHECKOUT> `
  --output-dir <EMPTY_OUTPUT_DIRECTORY>
```

Optional verification adds:

```text
--verify-against <COMMITTED_PACKET> --comparison-report <NONCANONICAL_REPORT>
```

The command validates tracked-input hashes, exact identity, temporal metadata,
exactness proofs, frozen/current comparators, preserved metrics, and packet
inventory. Generation then seals all 27 nonmanifest files and creates
`MANIFEST.json` without self-reference. No refresh-manifest or post-build
correction mode exists.
