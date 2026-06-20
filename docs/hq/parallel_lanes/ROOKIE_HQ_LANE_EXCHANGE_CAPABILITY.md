# Rookie HQ Lane Exchange Capability

Rookie HQ can publish one Rookie-owned Lane Exchange package:

- `rookie_hq/frozen_rookie_mock_input`

This capability is manual-use only. It does not change draft-board formulas, board order,
scores, production app wiring, veteran/player Outcome logic, R-ACC outputs, or the manual
draft kit.

## Exchange Role

Rookie HQ is the producer for frozen rookie mock input snapshots. The package is written to
the local-only exchange hub:

```text
C:\NWR_SHARED_DATA\lane_exchange\rookie_hq\frozen_rookie_mock_input\
```

Downstream lanes may consume the package only after validating the manifest, SHA256, row
count, approval status, and allowed-use fields under the Master Lane Exchange contract.

## Candidate vs Approved

Publishing without an approval flag writes:

```text
latest_candidate.json
```

Publishing with the explicit approval option also writes:

```text
latest_approved.json
```

`latest_candidate.json` is not trusted for draft decisions. `latest_approved.json` is written
only when the operator passes `--approve`.

## Publisher Command

Use fake/temp data for dry runs unless Master explicitly approves a real snapshot.

```powershell
python scripts/rookie_lane_exchange_publish_check.py `
  C:\path\to\fake_rookie_mock_input.csv `
  --exchange-root C:\path\to\temp_lane_exchange `
  --snapshot-label fake_candidate_check
```

Approved publication is manual:

```powershell
python scripts/rookie_lane_exchange_publish_check.py `
  C:\path\to\approved_rookie_mock_input.csv `
  --approve
```

## Manifest Validation

The Rookie utility validates the Lane Exchange required fields:

- `source_lane`
- `source_repo`
- `source_branch`
- `source_head`
- `package_name`
- `schema_version`
- `data_file`
- `row_count`
- `sha256`
- `created_at`
- `approval_status`
- `approved_for`
- `allowed_use`
- `forbidden_use`
- `contains_private_value`
- `contains_market_data`
- `contains_adp`
- `notes`

It computes SHA256 from the copied payload and computes `row_count` for CSV and feasible JSON
payloads. The publisher refuses packages outside Rookie ownership.

## Guardrails

- Do not commit exchange snapshots.
- Do not commit `C:\NWR_SHARED_DATA` contents.
- Do not copy `local_exports` into Git.
- Do not publish packages owned by Outcome, Mock Draft, Drop Decision, Deployment V2,
  Trading Lab, QA/Data Hygiene, Master, or any non-Rookie lane.
- Do not use this publisher to run simulations, tuning, formula changes, ranking changes, or
  production app wiring.
- R-ACC and manual draft kit outputs remain manual-use only and formula/order unchanged.
