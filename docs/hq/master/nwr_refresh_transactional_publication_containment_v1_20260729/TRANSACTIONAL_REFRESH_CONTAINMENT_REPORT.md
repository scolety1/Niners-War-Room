# Transactional Refresh Containment Report

Review date: 2026-07-29.

Starting canonical HQ was
`5258e37998f76236fa55b097cb351fe8900e02c1`, tree
`71aa3ec685796b7ab276644714affffb49958a15`. The bounded implementation
commit is `9b725b0a57ab1e87c1d69b3053958155eb6bdb5a`, tree
`70d4c341b8d657c308f6a4c59d62ad5f625967f4`. A detached worktree created
directly from remote HQ independently adopted the implementation as
`350d17230dd5f571409e49b0a33c33e4571f75d8`; its tree is identical.

The release-blocking five-file replacement boundary is removed. A refresh now
writes the exact five artifacts into one staging generation, flushes and
validates them, writes a hashed generation manifest, renames the complete
directory into `generations`, and commits visibility through one
`current_generation.json` replacement. Before that replacement the old
generation remains current; after it the new complete generation is current.

The publisher authenticates the canonical safe-root chain with directory
handles, records final handle paths, volume serials, file IDs, and reparse
attributes, holds governed ancestors without delete sharing, revalidates
identity before both commit operations, and binds Windows renames to validated
parent handles. Readers authenticate the pointer, manifest, exact inventory,
sizes, and SHA-256 values and load all five payloads while the governed handles
remain held.

Synthetic fault injection passed 24/24 mandatory cases. Reparse and alias
negative controls passed 13/13, including
`POST_VALIDATION_REPARSE_SWAP_FAILS_CLOSED`. The exact legacy second-replacement
failure produced one new and four old files; the new design exposed no
individual output and retained the old pointer on pre-commit failure.

Both implementation and independent review worktrees passed 98 focused tests,
2,875 Hermetic tests, changed-file Ruff, Python compilation, PowerShell
parsing, and Git whitespace checks. LocalData returned
`BLOCKED_MISSING_LOCAL_TEST_PACK` with native exit 4 in both worktrees.

No provider was called. No refresh was executed. No security scan was run. The
scheduled task remained disabled. Production ranking change is `NONE`;
production Outcome change is `NONE`.
