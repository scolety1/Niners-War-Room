# Merge Order Plan

## Merge Classes

### 1. Evidence Packet Merge

Evidence packets include reports, source traces, source maps, prompts, charters, registries, scorecards, and review-only matrices. These should merge before scripts or production proposals when they are complete and guardrail-clean.

### 2. Review-Only Script Merge

Review-only scripts may merge only after their owning evidence packet defines scope, inputs, outputs, leakage policy, and guardrails. Script merges must include tests or parse checks and must not change production runtime behavior.

### 3. Production Change Merge

Production formula, ranking, runtime, UI, or default-sort changes require a separate approved lane. They must not be bundled with evidence packets or review-only scripts.

### 4. Source Promotion Merge

Source promotion requires a separate source-admission lane with identity, coverage, leakage, missingness, and source-truth review. It must not be bundled with feature research, tournament evidence, or formula changes.

## Recommended Future Merge Order

1. Merge this orchestration packet if accepted.
2. Merge HQ 2 Source-Safe Feature Tournament V1 evidence packet if guardrail-clean.
3. Merge HQ 1 Experimental Feature Discovery Registry V1 if guardrail-clean and separated from HQ 2 outputs.
4. Merge HQ 1 Future Feature Tournament Registry V1 after the broad registry is stable.
5. Merge any review-only tournament runner only after its evidence packet and input/output ownership are accepted.
6. Merge position-specific candidate formula evidence only after review-only tournament evidence exists.
7. Merge production changes only after separate approval and never as part of research-artifact merges.

## Dependency Notes

- HQ 2 can proceed first because the prior-year baseline failure response is immediate and narrow.
- HQ 1 can proceed in parallel only if it writes to distinct broad-discovery paths and does not create immediate challenger scorecards.
- Later tournament runner lanes should wait until HQ 1 and HQ 2 naming conventions are reconciled.
- Production promotion should wait until exact formula status, source admission, and benchmark evidence are all accepted.
