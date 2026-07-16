# Independent Security Review

## Finding DG021

**Title:** Mutable Codex profile crosses the workspace sandbox through supervisor command execution

**Finding / instance:** `csf_64252c7850e1f7649842646d`; `occ_ab6d2639663c51a5842c430e`; candidate `CAND-review-020-02`; ledger `DG021`

**Discovery locations:** guardrail root control lines 35-50; night-loop sink lines 124-130; outcome lines 193-194 in the captured snapshot

**Method:** safe disposable profile reproduction, focused integration controls, and exact source-to-sink review

**Confidence:** high

- [x] Worker-controlled profile input is realistic in the original full-auto workflow.
- [x] Original post-edit policy reload and expression sink are present.
- [x] Patched privileged policy is frozen and authenticated before worker execution.
- [x] Patched executable, arguments, directory, commit, and push authority are worker-inaccessible.
- [x] Repository command text remains inert while legitimate structured execution passes.

**Evidence:** original guardrail exit `0` after profile redefinition; marker deliberately not executed; original reload and `Invoke-Expression` statically present. Patched controls 08-12 and 18-20 pass; no expression sink remains.

**Disposition:** prepatch `reportable`, survives `yes`; implementation `FIXED`.

**Remaining uncertainty:** actual hostile model steering and operator privilege were not exercised because they are unnecessary to prove the deterministic control/sink path.

**Minimal next step:** none for finding closure; retain independent review before any future privilege re-enable.

**Validation artifact:** this packet and `EXPLOIT_AND_BYPASS_REVALIDATION.md`.

## Finding DG022

**Title:** Staged and untracked changes bypass the automated Git guardrail

**Finding / instance:** `csf_357eb1a79de80c711e413696`; `occ_c65931e203e50f752d857365`; candidate `CAND-review-020-03`; ledger `DG022`

**Discovery locations:** guardrail root controls lines 19-31 and 54-80; night-loop commit/push sink lines 226-231 in the captured snapshot

**Method:** realistic disposable Git-state reproduction, 20 focused controls, exact-tree positive control, and alternate-bypass review

**Confidence:** high

- [x] Staged and non-ignored untracked worker input is realistic.
- [x] Original plain-diff control omits both states before broad staging.
- [x] Patched review consumes the complete cached candidate and records `write-tree`.
- [x] Every post-approval drift and Git-binding mismatch rejects.
- [x] Production commit, push, and force paths are absent.

**Evidence:** original guardrail exit `0`, visible set `safe.txt`, omitted set `package.json` and `untracked.txt`, prospective broad-staged set all three. Patched controls 01-07 and 13-20 pass.

**Disposition:** prepatch `reportable`, survives `yes`; implementation `FIXED`.

**Remaining uncertainty:** automatic merge/deploy impact was not established and does not affect the medium guardrail-bypass closure.

**Minimal next step:** none for finding closure; actual unattended commit/push remains disabled.

**Validation artifact:** this packet and `EXPLOIT_AND_BYPASS_REVALIDATION.md`.

## Closure table

| Ledger | Instance | Root control | Source | Sink/control | Disposition | Counterevidence / gap | Survives |
|---|---|---|---|---|---|---|---|
| DG021 | occ_ab6d2639663c51a5842c430e | captured guardrail 35-50 | worker-edited profile | captured `Invoke-Expression`; patched frozen argv | reportable prepatch; fixed candidate | no hostile model run; deterministic path proven | yes prepatch; no after fix |
| DG022 | occ_c65931e203e50f752d857365 | captured guardrail 19-31,54-80 | staged/untracked worker bytes | captured broad commit; patched cached tree | reportable prepatch; fixed candidate | no remote consequence required | yes prepatch; no after fix |

The scan bundle was read-only by user instruction. These visible per-finding receipts replace writes to its ledger/report paths without altering the supplied evidence.
