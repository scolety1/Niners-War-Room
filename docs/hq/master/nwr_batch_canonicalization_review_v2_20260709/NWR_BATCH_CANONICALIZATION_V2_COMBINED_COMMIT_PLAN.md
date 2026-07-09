# NWR Batch Canonicalization V2 Combined Commit Plan

## Decision

Create one local combined canonicalization commit parented on:

`c90661778e0513e988b8a593045609d4433059c9`

Do not push in this lane.

## Include

Include only packets classified as:

`CANONICALIZE_NOW_DOCS_ONLY`

Included source packets:

1. Confidence Cap Component Signal Test V1
2. Role Archetype Receipt Regeneration Pilot V1
3. Role Archetype Component Signal Test V1
4. Role Archetype Master Review V1

Also include this V2 Master HQ review packet.

## Exclude

Exclude anything outside `docs/hq/`.

Exclude runtime, app, ranking, model scoring, formula code, source-gate, canonical board artifact, and `local_exports` paths.

Exclude any source promotion, production/model-use approval, Formula Gauntlet tournament, tuning, exact replay, receipt regeneration, or ranking integration work.

## Expected Local State

After commit, the branch should be one commit ahead of `origin/work/hq-parallel-control`, zero behind, with a clean worktree.
