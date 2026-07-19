# Hermetic and LocalData final results

## Exact candidate

Candidate commit: `51f2e96bd00ca133abb738b7a1082980b1db979a`

Candidate tree: `336fb52f3dedfe18da04b54ef54885be6aa06dec`

The canonical Hermetic command completed with:

- deterministic bootstrap controls: 13/13;
- deterministic pack hash: `6e7e2ff88de7e1fc8bd620657a619e16d1d183bb117d9c9c631477ab811ad98f`;
- security controls: 20/20;
- Python tests: 2,648 passed;
- owned Ruff: pass;
- exit code: 0;
- skips: 0;
- xfails: 0;
- xpasses: 0.

Three short-path exact-tree bootstraps reproduced the same deterministic hash. Full application, script, source, and test compilation passed. Changed-file Ruff passed with zero findings. Full-tree Ruff was intentionally compared against starting HQ with cache disabled: both trees reported the same 4,443 pre-existing findings with identical rule counts, so the differential is zero.

## LocalData

The separate canonical LocalData gate returned exactly:

`BLOCKED_MISSING_LOCAL_TEST_PACK`

Captured exit code: `4`.

LocalData is not passed, skipped, xfailed, xpassed, waived, synthesized, copied, inspected, or counted in Hermetic. The absence is an accepted V1 limitation, and supported behavior fails closed without the private pack.
