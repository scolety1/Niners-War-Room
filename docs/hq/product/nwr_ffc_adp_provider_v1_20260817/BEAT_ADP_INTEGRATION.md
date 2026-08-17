# Beat ADP Integration

Beat ADP now evaluates every safely matched Draft Room row against the active FFC snapshot while keeping judgment and timing separate.

- NWR view: `STRONG VALUE`, `VALUE`, `ALIGNED`, `FADE`, or `STRONG FADE`.
- Draft timing: `TAKE NOW`, `VALID`, `REACH`, `WAIT`, or `ADP UNAVAILABLE`.
- Make-It-Back: separately labeled, bounded heuristic or unavailable.

Inputs include NWR rank, FFC expected pick, current and next owner pick, tier cliff, positional run, and roster context. External ADP never replaces the NWR rank.
