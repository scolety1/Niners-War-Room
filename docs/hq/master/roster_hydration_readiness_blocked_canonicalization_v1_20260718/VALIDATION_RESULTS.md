# Validation Results

Overall documentation review result: PASS. Hydration readiness remains blocked by stable admitted identity, and automated roster hydration is parked post-V1.

## Control plane and inventory

| Check | Result | Evidence |
| --- | --- | --- |
| Fetch and prune | PASS | All remote references fetched and pruned before review |
| Starting live HQ | PASS | `adc058512b389657830e86ad1abd4b85bebd7eea`; tree `00f6e7035fd81ad9341dd5605eb251ae375b785a` |
| Remote advance before review | NONE | Expected and actual HQ matched; no intervening commit |
| Source ancestry | PASS | Source parent is exact live HQ; zero behind and one ahead |
| Source worktree | PASS | Clean and unchanged at `f5c19c92fea87bd68dcc988ce41ffea3a118d8ab` |
| Source inventory | PASS | Exactly 23 added paths, all within the source packet |
| Implementation-path inventory | PASS | Zero app, service, schema, registry, identity, roster, configuration, test, LocalData, automation, protected, or frozen changes |

## Source, identity, scope, and fields

| Check | Result | Evidence |
| --- | --- | --- |
| Source registry | PASS | 36 rows; zero duplicate keys; zero firewall issues |
| Sleeper admission | PASS | players, rosters, and drafts_and_traded_picks are `ADMITTED_FACT` |
| Exact join | BLOCKED AS EXPECTED | Sleeper player ID to `dim_players.sleeper_id` to NWR `player_id` only |
| Tracked identity fixture | BLOCKED AS EXPECTED | 24 unique player IDs; zero populated Sleeper IDs |
| Tracked roster fixture | PASS AS SYNTHETIC ONLY | 24 rows; zero duplicate player IDs; zero missing synthetic dimension joins |
| Draft-pick fixture | PASS AS SYNTHETIC ONLY | 3 rows; zero duplicate source-coordinate tuples; no tracker canonical asset ID |
| Asset scope | BLOCKED AS EXPECTED | Active, rookie, veteran, taxi, IR, inactive/retired, and kicker coverage unproved; DST and picks lack approved exclusion or stable contract |
| Future field contract | PASS AS DOCUMENTATION | 34 unique fields; no implementation |
| Current roster fields | BLOCKED AS EXPECTED | 13 columns; governed slot/starter/taxi/IR/identity/lifecycle/integrity/timestamp/retention fields absent |
| League context | YELLOW AS EXPECTED | Canonical facts exist; runtime typed lineup, flex, bench, scoring, DST, phase IR, and taxi context incomplete |

## LocalData, route, trust, and packet integrity

| Check | Result | Evidence |
| --- | --- | --- |
| LocalData tier | BLOCKED AS REQUIRED | `BLOCKED_MISSING_LOCAL_TEST_PACK`; captured exit `4`; collection not started |
| Provider boundary | PASS | No live provider call, roster hydration, or production-data write |
| Roster route smoke | PASS | Route exists, navigation registration exists, and focused route/static tests passed |
| Focused test run | PASS | 77 tests passed in 14.69 seconds |
| Failure matrix | PASS | 24 unique scenarios with required stale, retained, partial, duplicate, unsupported, missing, gated, corrupt, and cross-surface states |
| Trust vocabulary | PASS | Existing Decision Trust Strip, Refresh Recovery, and retained-data terms reused exactly |
| Source packet CSV parse | PASS | 7 CSV files; all rows had the declared width |
| Source packet duplicate keys | PASS | Zero findings |
| Source manifest membership | PASS | 23 declared files matched 23 on-disk files |
| Source manifest hashes | PASS | 22 non-manifest hashes; zero failures; 91,645 canonical hashed bytes plus 4,102 manifest bytes |
| CSV formula-prefix scan | PASS | Zero findings |
| Privacy/secret scan | PASS | Zero private-key, AWS, GitHub, Slack, bearer-token, assigned-secret, or long-numeric-ID findings |

## Protection and preservation

| Check | Result | Evidence |
| --- | --- | --- |
| Frozen/prospective paths | PASS | 137 paths; zero diffs; case-insensitive-order aggregate matched `6d42096a0ddf0f270cf5ed4141647ac085fce5ca14c9187af97736eee0455611` |
| Explicit protected blobs | PASS | 9 checked; zero mismatches |
| Security automation | PASS | Zero changes under `.github`, `.codex`, or `scripts` |
| Primary preservation | PASS | Exactly five pre-existing DynastyProcess modifications; all five required SHA-256 values matched |
| Canonical packet inventory | PASS | Exactly the 18 required files and no other path |
| Canonical CSV parse and duplicate keys | PASS | All canonical CSVs parse; zero duplicate declared keys |
| Canonical manifest | PASS | Membership, SHA-256, and canonical byte counts validate for every non-manifest file |
| `git diff --check` | PASS | No whitespace errors |
| `git diff --cached --check` | PASS | No staged whitespace errors |

Final remote-advance, push, remote readback, clean status, and zero-ahead/zero-behind results are performed after this packet is committed, because those checks necessarily follow the immutable documentation artifact.
