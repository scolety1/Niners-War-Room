# Hermetic Bootstrap Contract

Command:

`powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\scripts\bootstrap-hermetic-test-pack.ps1 -RepoRoot . -Clean`

The only source is tracked `tests/fixtures/hermetic/local_export_pack_v1/`. The only output is an ignored owned `local_exports/hermetic_test_pack_v1*` subtree. Source hashes and sizes are validated before generation. Output bytes, manifest, marker, and SHA-256 receipt are deterministic and bounded.

`-Clean` removes four known owned files and empty owned directories; an unowned sentinel survives. `-VerifyOnly` detects corruption. Escape, reparse, untracked-source, rights, schema, version, hash, and size failures fail closed. There is no network, credential, arbitrary-disk discovery, or fallback path.

Contract result: `14 passed, 0 failed`, including a fresh disposable checkout and aggregate visibility assertion.
