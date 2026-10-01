# NWR Reliability Gauntlet

Date: 2026-10-01  
Branch: `upgrade/nwr-prospective-outcomes-v1-20260914`  
Dispatch HEAD verified before work: `7462cb7c`

## Disposition

**NOT YET TRUSTED for unattended release-gate restarts or guaranteed concurrent
Redraft profile activation.**

The new automated gauntlet proves that the backend entry point can cold-start
with cryptographic process identity, rejects a real bound-port conflict, remains
healthy under concurrent HTTP load, and never leaves either active-profile
pointer as partial JSON under the exercised concurrent-write races. It also
found two real gaps which are pinned as explicit expected-failure canaries:

1. `desktop/scripts/nwr_release_gate_smoke.ps1` still accepts readiness from
   any process answering `200` on the expected port. It does not verify that
   the `Start-Process` child survived, does not consume the child's startup
   identity record, and does not challenge `/startup-proof`. The exact
   stale-backend-reuse failure described in the cycle ledger can therefore
   still fool the release-gate wrapper.
2. Redraft's pointer writer publishes only complete JSON, but simultaneous
   `set_active_profile()` calls on Windows can contend while replacing the same
   destination and some calls fail with the service's persistence error. The
   last published pointer remains valid. This is an availability/serialization
   gap, not a half-written-JSON gap.

This is intentionally not labeled `TRUSTED` or `TRUSTED_WITH_LIMITATION`: the
first gap is the single failure class this pass was specifically required to
prove protected, and the real release-gate wrapper is not yet protected.

## Automated suite

New file: `tests/test_reliability_gauntlet.py`.

All spawned backends use `run_nwr_desktop_api.py`, OS-assigned high ports, and
test-local `NWR_REDRAFT_HOME`, `NWR_DYNASTY_LEAGUE_HOME`, `APPDATA`, and
`LOCALAPPDATA` roots. The suite never binds, probes, stops, or kills ports
18741, 18742, 1421, or 1422. Every spawned process is terminated in a `finally`
path.

### Cold start - PASS

`test_cold_start_is_healthy_and_cryptographically_identity_verified` starts a
fresh real Redraft backend on port `0` (the server selects an unused high port),
parses the runner's startup identity record, receives an authenticated
`/healthz` response, and validates a fresh `/startup-proof` HMAC over protocol,
mode, actual port, and challenge. This proves identity, not merely that some
listener returned `200`.

### Restart race - entry point PASS, release gate XFAIL

`test_restart_race_rejects_stale_listener_instead_of_trusting_its_200` starts a
separate dummy HTTP process first. The dummy binds an OS-assigned port and
returns `200` with an old-process identity. A real
`run_nwr_desktop_api.py` process is then launched against the same port.

The deliberately naive readiness request succeeds against the stale process,
reproducing the false-positive precondition from the ledger. The requested new
backend emits no startup identity and exits nonzero with the bind error. The
gauntlet therefore catches the stale listener by treating the launched process
and its identity record as authoritative.

`test_release_gate_restart_readiness_is_bound_to_the_launched_process` is the
expected-failure canary. It inspects the real release-gate readiness block and
requires both launched-process validation and `/startup-proof`. It remains
XFAIL because neither guard exists there today. This is not a test weakened to
match broken behavior; it is an executable remediation contract.

### Concurrent pointer writes - JSON integrity PASS, Redraft writer XFAIL

The confirmed real paths are:

- Redraft: `<redraft store>/active_profile.json`, normally
  `local_exports/redraft_v1/active_profile.json`.
- Dynasty: `<dynasty league store>/active_league_profile.json`, normally
  `local_exports/dynasty_v1/active_league_profile.json`.

Both real persistence functions use a temp file followed by `os.replace`.
Redraft uses a UUID temp name. Dynasty uses PID plus a second-resolution UTC
stamp.

The gauntlet invokes the public `set_active_profile()` and
`set_active_league_profile()` functions concurrently against isolated stores.
It validates the destination after each race and rejects leftover temp files.
The Dynasty test additionally forces every writer into the same timestamp
bucket to exercise its real temp-name collision shape.

- Both destination files remained complete, parseable JSON with a valid
  `profile_id`: PASS.
- Dynasty's forced same-second concurrent write exercise completed without a
  writer error on this Windows run: PASS.
- Redraft had one or more Windows destination-replace contention failures in
  repeated 32-writer waves, while the destination remained valid: XFAIL canary
  for the missing serialization/retry behavior.

The suite does not claim power-loss durability or fsync semantics; it covers
the requested concurrent in-process writer race and JSON integrity.

### Concurrent HTTP requests - PASS

`test_concurrent_http_requests_do_not_crash_or_corrupt_test_local_state` starts
a separate real backend, warms bootstrap once, then releases 32 requests at the
same barrier: 24 authenticated `/healthz` requests and eight authenticated
`/api/v1/bootstrap` requests. Every response is HTTP 200 with a JSON data
object, the process remains alive, a final health check passes, every JSON file
under the isolated Redraft state root parses, and no temp file remains.

## Results

Targeted gauntlet:

```text
6 passed, 2 xfailed in 4.15s
```

Ruff 0.14.1:

```text
All checks passed!
```

Gauntlet plus the requested standard baseline
`tests/test_desktop_application_api.py`:

```text
56 passed, 2 xfailed, 1 failed in 59.34s
```

The single failing node remains the existing
`test_dynasty_facade_composes_real_governed_workflows`. The baseline file is
therefore still 50 passed / 1 failed. In this environment `marketMatched` was
230, so that assertion passed and the same test next failed on its stale exact
ranking-key set omitting the already-shipped additive
`currentStatusOverride` field. This is the same pre-existing test node, not a
new reliability-gauntlet regression.

`git status --short -- docs/model_v4 local_exports/model_v4` was empty before
and after the combined run. No generated data pack, governed formula, base
board, projection snapshot, private league payload, owner AppData, or live
provider write path was touched.

## Required follow-up

1. Make release-gate readiness process-bound: fail immediately if the launched
   child exits, parse and validate its startup identity record, and verify a
   fresh `/startup-proof` response using that run's private proof key before
   any bootstrap readiness request is trusted.
2. Serialize Redraft active-pointer writes (or add a bounded Windows replace
   retry/lock around this single marker) so all concurrent activation calls
   succeed while preserving the current atomic publication property.
3. Remove the two XFAIL dispositions only after the corresponding canaries
   pass against the real mechanisms.

Master Requirement Ledger section 7.27 is therefore **partially closed with
real automated coverage**, but its unattended-restart claim remains open for
the precise release-gate identity reason above.
