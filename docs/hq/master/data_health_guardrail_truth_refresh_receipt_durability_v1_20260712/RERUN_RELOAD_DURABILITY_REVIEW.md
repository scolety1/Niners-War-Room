# Rerun and Reload Durability Review

## Supported boundaries

| Boundary | Result | Evidence |
|---|---|---|
| Ordinary Streamlit rerun | Supported | Component AppTest reruns against the same persisted receipt and keeps the same receipt ID. |
| Page navigation away/back | Supported in the same local app | Both affected pages load the same orchestrator-owned receipt; controlled browser navigation from Refresh Data to Settings / Data Health retained the matrix receipt. |
| Browser reload | Supported when reconnecting to the same local app/root | Controlled browser reloads re-read receipt metadata from disk; no session-only receipt is required. |
| Fresh local application process | Supported on the same machine/account/root | Store test constructs a new `Path` and reloads identical validated JSON; a fresh AppTest instance renders the same receipt ID. |
| Missing storage | Supported fail-closed | Returns `MISSING`; UI says no current outcome is inferred. |
| Corrupt/truncated latest | Supported fail-closed | Returns `CORRUPT`, quarantines the latest, and separately reports a validated backup when present. |
| Oversized latest | Supported fail-closed | Rejects before JSON parsing at greater than 2 MiB and quarantines under normal load. |
| Unsupported schema | Supported fail-closed | Returns `UNSUPPORTED_SCHEMA`, preserves the file, and never parses it as V1 truth. |
| Corrupt latest and backup | Supported fail-closed | Neither payload is usable. |

Opening either affected page does not invoke refresh execution. Route-smoke tests hash every pre-existing file under the receipt root before and after page open and require an identical snapshot.

## Unsupported boundaries

Durability is not claimed after local state deletion, receipt-root relocation, machine/user/account change, deployment replacement, cloud replication, or across distributed concurrent writers. No external database, provider API, scheduled job, retry, or hidden refresh was added.

## Mutation note

Receipt validation is read-only except for the bounded invalid-latest quarantine lifecycle. The Data Health service uses a side-effect-free validation read so the page receipt panel can show and quarantine the same invalid artifact consistently. Neither action mutates source state or production data.
