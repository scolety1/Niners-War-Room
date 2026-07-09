# NWR Batch Canonicalization Combined Commit Plan

## Plan

Create one local combined canonicalization commit parented on:

`a57b33e1c2cd55bc61d0c0a32cb48ed554b776cc`

The commit should include only:

- packets classified `CANONICALIZE_NOW_DOCS_ONLY`
- this batch canonicalization review packet

The commit must not include:

- parked packets
- app/runtime implementation changes
- ranking/model/source-gate behavior changes
- canonical `local_exports` writes
- duplicate or superseded packets

## Included Packet Count

`22`

## Parked Packet Count

`3`

## Superseded Packet Count

`1`

## Commit Message

Recommended local commit message:

`docs: batch canonicalize NWR review packets v1`

## Push Status

No push is approved by this review. A separate guarded batch push lane is required.
