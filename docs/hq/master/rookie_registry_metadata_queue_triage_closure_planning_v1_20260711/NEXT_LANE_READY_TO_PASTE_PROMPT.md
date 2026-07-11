# Next Lane Ready-to-Paste Prompt

## NWR Rookie Registry Protected Source Proof Preparation V1

This is a documentation-only proof-preparation lane for `batch_836e8658fea7760a7278dd66` from `docs/hq/master/rookie_registry_metadata_queue_triage_closure_planning_v1_20260711/`.

Do not close, modify, delete, or rewrite any canonical queue row. Do not add active mappings, register or promote sources, activate deferred candidates, make source/use decisions, resolve identities, populate player/alias/identity/evidence/player-value rows, copy protected content, expose local/private locators, modify runtime or UI, change rankings/formulas/recommendations/production data/plugins/draft logic/frozen-2026 artifacts, or push.

Before work:

1. Fetch all remote references and verify the live head of `work/hq-parallel-control`.
2. Start from the local planning packet commit if available; otherwise require the packet and its manifest to be present byte-for-byte.
3. Verify the mapping contract hash `19bb737de35f476ad39bff50d41f25e5ec6ef3b88dacd48d23b47917960fa264`, queue contract hash `e6c5d46f114afb4edc59b007e3422c0e543e1a3403be6708e93b610d67c30075`, and queue hash `9ef64f1a3a06dc96a968da37bc53e825de656b0545e177c6d9c899485db6971f` as canonical Git blobs.
4. Create a new isolated worktree and branch. Commit locally only; do not push.

Scope exactly the two rows selected by `batch_836e8658fea7760a7278dd66` in `QUEUE_TRIAGE_RECONCILIATION.csv`. Confirm both are live-HQ, `SUPPORTING_EVIDENCE`, `ARTIFACT_SOURCE_LINK_MISSING`, and `PARTIAL_PROOF_ONLY`. Confirm the third protected exact-hash candidate is excluded because it is conflict-state.

Produce a decision-ready proof-preparation packet that:

- records the existing exact hash candidate only by canonical reference and hash;
- confirms the packet source reference is not a registered canonical source endpoint;
- defines the exact canonical source endpoint registration request without registering it;
- defines the exact protected-scope source/use authorization request without deciding it;
- defines the exact durable artifact/source receipt or manifest relationship required;
- specifies zero authority, source-promotion, and use-permission effects;
- provides mechanical validation, stop, rollback, no-mutation, privacy, protected-path, and frozen-artifact proofs.

Required verdict: use a yellow proof-preparation-ready verdict unless both rows already have all required canonical endpoint, authorization, relationship, hash, rights/locality, and append-only-event prerequisites. Even if prerequisites appear complete, do not close; instead recommend a separately authorized closure lane with a maximum of two rows.

Validation must prove: canonical queue rows 5,147; closed 0; automatically closed 0; active artifact-to-authority links 113; other active relationship types 0; deferred candidates 28 and inactive; explicit source/use decisions 0; player/evidence rows 0; no queue or canonical registry mutation; no source promotion; no identity resolution; no protected/frozen change; all CSV/JSON parse; duplicate keys 0; `git diff --check`; `git diff --cached --check`; and clean worktree after local commit.
