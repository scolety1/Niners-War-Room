# Maintenance Queue

Fleet-managed intake for bug triage, flaky tests, performance regressions, validation hardening, and technical debt.

- [ ] Keep validation and model tests current as each formula or importer lands. [class:bugfix risk:low mode:single scope:tests/,src/,docs/codex/ acceptance:powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1]
