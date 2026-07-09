# Data Hygiene Immediate Work Queue

This is a proposed queue only. Do not execute these items from this charter packet.

## 1. Model v4 Missing Historical Receipt Chain

- Purpose: identify missing source receipts, hashes, local_exports dependencies, and rebuild blockers for Model v4 historical inputs.
- Why Data Hygiene owns it: receipt chain, reproducibility, missing-file and source-trace audit.
- Current known blocker: historical upstream receipt chain is incomplete.
- Expected output packet: `docs/hq/data_hygiene/model_v4_historical_receipt_chain_audit_v1_YYYYMMDD/`
- Master HQ handoff condition: any source promotion, model-use approval, or canonical rebuild decision.
- Blocked actions: no model tuning, no weight changes, no production claims.

## 2. Formula Gauntlet Data Readiness Follow-Up

- Purpose: prove candidate input presence, receipt chains, missingness, leakage safety, and rebuildability before Formula Gauntlet work.
- Why Data Hygiene owns it: data readiness gate and leakage/rebuild audit.
- Current known blocker: Formula Gauntlet cannot safely rely on inputs without source receipts and use gates.
- Expected output packet: `docs/hq/data_hygiene/formula_gauntlet_data_readiness_v1_YYYYMMDD/`
- Master HQ handoff condition: Formula Gauntlet wants to score, tune, or promote formulas.
- Blocked actions: no tournaments, no formula winner selection, no ranking changes.

## 3. Route/YPRR/TPRR Source Admission Support

- Purpose: audit whether a rights-cleared route denominator source exists and can be admitted.
- Why Data Hygiene owns it: source trace, licensing, identity, coverage, leakage, denominator safety.
- Current known blocker: no admitted route/YPRR/TPRR source; no fake route proxies.
- Expected output packet: `docs/hq/data_hygiene/route_source_admission_support_v1_YYYYMMDD/`
- Master HQ handoff condition: Route Recovery asks to use a source or promote route metrics.
- Blocked actions: no route recovery, no TPRR/YPRR construction, no participation proxy.

## 4. Current-Board Recovered Input Bundle Preservation

- Purpose: preserve receipt chains, board/input manifests, hashes, and rebuild instructions for recovered current-board inputs.
- Why Data Hygiene owns it: board/input manifest, hash, provenance, and rebuildability evidence.
- Current known blocker: recovered inputs can be useful but may lack complete upstream receipts.
- Expected output packet: `docs/hq/data_hygiene/current_board_input_bundle_preservation_v1_YYYYMMDD/`
- Master HQ handoff condition: board/ranking may become production-active or canonical.
- Blocked actions: no ranking changes, no hidden sort, no app behavior.

## 5. Historical Labels / Source Coverage Audit

- Purpose: audit label source provenance, row counts, season coverage, missingness, and leakage safety for historical labels.
- Why Data Hygiene owns it: label source trace and historical replay eligibility.
- Current known blocker: historical labels require strict source coverage and no post-outcome leakage.
- Expected output packet: `docs/hq/data_hygiene/historical_labels_source_coverage_audit_v1_YYYYMMDD/`
- Master HQ handoff condition: labels may support promotion, benchmarks, or model training.
- Blocked actions: no training, no model approval, no production accuracy claim.

## 6. local_exports / Handoff Artifact Inventory Policy

- Purpose: define which local exports are ignored, which need transfer manifests, and which can become compact review artifacts.
- Why Data Hygiene owns it: missing-file blockers, local-only dependency audit, and reproducibility.
- Current known blocker: local_exports can be essential but not tracked.
- Expected output packet: `docs/hq/data_hygiene/local_exports_handoff_policy_v1_YYYYMMDD/`
- Master HQ handoff condition: canonicalization requires a local-only artifact.
- Blocked actions: no raw local_exports tracking, no unsafe copy.

## 7. Source Receipt-Chain Enforcement Across Future Lanes

- Purpose: ensure future source, replay, formula, and app lanes use HQ1 receipt fields and Data Hygiene handoff format.
- Why Data Hygiene owns it: governance standard enforcement.
- Current known blocker: lanes may produce useful artifacts without complete receipt chains.
- Expected output packet: `docs/hq/data_hygiene/source_receipt_chain_enforcement_v1_YYYYMMDD/`
- Master HQ handoff condition: enforcement changes lane routing or canonical merge criteria.
- Blocked actions: no production approval, no lane merge decisions.
