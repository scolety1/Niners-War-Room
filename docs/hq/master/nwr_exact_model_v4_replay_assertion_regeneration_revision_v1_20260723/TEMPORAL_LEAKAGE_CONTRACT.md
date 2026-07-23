# Temporal leakage contract

Every historical feature record resolves these required fields:

- exact `player_id`;
- input and target seasons;
- fixed as-of boundary;
- feature family and field name;
- tracked source authority;
- source season;
- availability classification.

The target season must equal input season plus one. Source season may not exceed
input season. Missing or contradictory season, authority, as-of, family, or
availability metadata fails closed. Current-only ADP, current-board rank or
score, target-season scores/games, future production, and unsupported
classifications are inadmissible.

The canonical mart is hash-bound before any permitted in-memory order
perturbation. Normal lagged proxy and deterministic baseline records remain
accepted and reproduce their prior metrics.
