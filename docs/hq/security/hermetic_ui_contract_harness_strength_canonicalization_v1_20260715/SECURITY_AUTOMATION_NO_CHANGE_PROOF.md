# Security Automation No-Change Proof

Starting HQ and the adopted candidate have identical Git blob IDs and working
file SHA-256 values:

| Path | Git blob | SHA-256 | Result |
|---|---|---|---|
| `scripts/codex-guardrails.ps1` | `c65ae12b9a1f9349d433987c573aea8ebdeb586d` | `d2825ee91f8884ae5e841db6cc136c0670d05045ee45eb2f7e6d1167f5a8b14c` | byte-identical |
| `scripts/codex-night-loop.ps1` | `dbf55b2900f4400036a556ca88f148bdca695fbf` | `81d6debf17dbb2cb56c109526ab30b268da5282b187a0aa4971477f214303475` | byte-identical |
| `docs/codex/PROFILE.json` | `7d82bef9251a3c5293d3fe6b0ae701fdc7c2f125` | `d33a07da381c3b3ed3856881fba1a825e6b96ee82689ec66b64a4c2434621d9c` | byte-identical |

The diff under `scripts`, `docs/codex`, `.agents`, and `.github` is empty.
No guardrail, profile, auto-commit, auto-push, bootstrap, or LocalData behavior
was changed by Phase 1.

Result: `PASS_SECURITY_AUTOMATION_BYTE_IDENTITY`.
