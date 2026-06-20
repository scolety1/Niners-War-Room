# Trading Lab Lane Exchange Capability

Date: 2026-06-20

Lane: Trading Lab

Branch: work/trading-lab

Purpose: define Trading Lab's safe local Lane Exchange behavior for fantasy
trade research snapshots.

## Source Documents Read

- Master contract:
  `C:\NWR\Niners-War-Room\docs\hq\parallel_lanes\NWR_LANE_EXCHANGE_V0_CONTRACT.md`
- Local-only registry:
  `C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json`

The exchange hub and registry are local-only. They must not be committed.

## Trading Lab Exchange Role

Trading Lab is a future producer of its own fantasy trade research package:

- Owned package: `trading_lab/trade_research_snapshot`
- Registry status: `requires_explicit_approval_later`
- Publish posture: disabled by default unless the registry and caller explicitly
  allow publication.

Trading Lab is not currently registered as a standing consumer of any package.
It may validate approved exchange manifests for manual research readiness only
when a package is explicitly supplied to the readiness tool.

## Read Behavior

Trading Lab may read only approved exchange pointers:

- Allowed pointer: `latest_approved`
- Refused pointer: `latest_candidate`

The lane-local validator fails closed when:

- the pointer is missing
- the pointer references a manifest outside the local exchange hub
- the manifest is malformed
- required fields are missing
- `approval_status` is not `approved`
- the requested allowed use is not present
- the referenced file is missing
- `sha256` does not match
- `row_count` does not match

Presence of a file in the exchange hub is never treated as approval.

## Publish Behavior

Trading Lab can publish only its own research snapshot package:

```text
trading_lab/trade_research_snapshot
```

Publication is refused unless explicit publish approval is passed in addition to
the registry showing that Trading Lab owns the package. This implementation does
not publish real data during tests. Tests use temporary directories only.

## Paper-Research Limits

This capability is for fantasy football trade review support only. It does not
add:

- broker integration
- credentials, secrets, account keys, or tokens
- real-money trading
- broker orders
- automated execution
- production investment advice
- public deployment
- external provider ingestion
- automated fantasy trade submission

Trading Lab remains a fantasy football trade value calculator and trade package
review lane.

## Files Added

- `src/trading_lab/trading_lab_lane_exchange.py`
- `scripts/trading_lab_lane_exchange_readiness_check.py`
- `tests/test_trading_lab_lane_exchange.py`
- `docs/hq/parallel_lanes/TRADING_LAB_LANE_EXCHANGE_CAPABILITY.md`

## Operator Notes

Use the readiness script to inspect role information and validate explicitly
requested approved packages:

```powershell
python scripts/trading_lab_lane_exchange_readiness_check.py `
  --package league_state/nwr_picks `
  --allowed-use trade_lab_research_review
```

Do not use `latest_candidate` for any Trading Lab decision or review result.
Do not copy exchange snapshots into this repository. Do not commit exchange hub
contents.
