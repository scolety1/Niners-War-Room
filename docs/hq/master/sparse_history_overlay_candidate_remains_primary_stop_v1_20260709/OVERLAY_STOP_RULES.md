# Overlay Stop Rules

Active overlay testing should stop unless the user explicitly authorizes a new direction.

Preserved stop rules:

- Do not test more overlay families.
- Do not stack overlays.
- Do not integrate overlays into rankings.
- Do not run review-only ranking simulation.
- Do not promote `REFINE_005_A_EARLY_ROLE_015` to production/model-use.
- Do not change production rankings.
- Do not change app/runtime/model behavior.
- Do not promote sources.
- Do not push or merge.
- Do not write to canonical `local_exports`.
- Do not create hidden sort or recommendation logic.

Reason:

The broader overlay batch did not improve on the accepted sparse-history primary overlay candidate. The best batch policy row had net miss reduction `8`, and the best individual overlay family had net miss reduction `6`, while `REFINE_005_A_EARLY_ROLE_015` remains accepted at net miss reduction `16`.
