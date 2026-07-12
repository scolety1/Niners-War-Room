# Next Three Lanes

These lanes are ordered after the immediate Trading Lab lane. They are not authorized to run concurrently.

## 1. Player Compare Compact-Width and Accessibility Hardening V1

Classification: `READY_NOW_MODERATE_RISK`

Purpose: harden the dense, high-use comparison surface at compact widths and for keyboard/screen-reader use while preserving existing admitted facts, uncertainty, caveats, and neutral decision support.

Bounded outcome:

- verify information order and legibility for two to four players at compact widths;
- ensure tabs, selectors, caveats, and status messages have accessible names and keyboard behavior;
- prevent clipped evidence/provenance content;
- add focused rendered checks where feasible;
- preserve all current comparison semantics.

Stops: no winner logic, ranking/formula changes, new source data, saved/export workflow, or plugin content. Saved worksheets remain a separate design-first candidate.

## 2. Data Health Guardrail Truth and Refresh Receipt Durability V1

Classification: `READY_NOW_MODERATE_RISK`

Purpose: make operational safety claims truthful and recoverable.

Bounded outcome:

- inspect unstaged, staged, and untracked changes in explicitly protected path families;
- report unknown/red, never green, when Git diagnostics fail;
- replace the hard-coded no-mutation green result with evidence-derived status;
- atomically write latest refresh status and source manifests;
- recover a corrupt latest receipt only from the newest valid archive;
- add deterministic tests for staged/untracked changes, Git failure, interrupted writes, corrupt latest, archive fallback, and no-valid-receipt behavior.

Stops: no refresh source execution change, source admission, ranking/formula behavior, recovery-UX recreation, or broad deprecation cleanup.

## 3. Roster Weakness Tracker Admitted-Roster Hydration Design and Readiness V1

Classification: `NEEDS_DESIGN_FIRST`

Purpose: design a safe way to reduce manual roster re-entry using only existing admitted roster facts.

Required design outputs:

- exact admitted inputs and stable identity keys;
- clean-checkout missing-pack and empty-roster behavior;
- ambiguous/stale player handling without name fallback;
- manual override ownership and auditability;
- no-inference boundary for lineup slots and team strategy;
- fixture and test plan;
- a go/no-go implementation verdict.

Stops: this lane must not implement hydration; infer lineup slots; classify contender/rebuilder status; calculate replacement level; use Flaim; or change rankings, formulas, sources, or roster authority.

## Sequencing rule

After each lane:

1. merge-review it independently against then-current HQ;
2. reconcile the remaining scorecard;
3. confirm the next lane is still highest value;
4. do not assume this ordering survives newly discovered evidence.
