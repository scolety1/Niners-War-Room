# Sparse-History Overlay Ranking Simulation Blocker Canonical

Review-only ranking simulation remains blocked / not justified.

Reason:

The Sparse-History Overlay Candidate Preservation V1 packet preserved review-only overlay candidates, but did not authorize board simulation. The strongest result is a miss-reduction overlay candidate, not a validated ranking-simulation candidate.

Preserved blockers:

- production/model-use remains blocked
- rankings integration remains blocked
- app/runtime behavior remains unchanged
- hidden sort / recommendation logic remains blocked
- source promotion remains blocked
- canonical `local_exports` mutation remains blocked
- push/merge was not performed

Future ranking simulation can only occur if a later explicit readiness-gate lane authorizes it.
