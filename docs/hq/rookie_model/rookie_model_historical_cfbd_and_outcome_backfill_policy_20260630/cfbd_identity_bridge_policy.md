# CFBD Identity Bridge Policy

## Verdict

Historical CFBD identities remain review-only and unapproved for model input. Fuzzy matching cannot
approve identities.

## Approved Evidence Hierarchy

1. Stable CFBD player ID linked to the drafted player by an approved crosswalk.
2. Exact full-name match plus exact position plus exact college/team timeline for seasons before
   the NFL Draft.
3. Secondary corroboration from PFR/CFB IDs, official school roster timeline, or approved transfer
   timeline.
4. Human review record that explicitly marks the identity as review-only approved.

## Exact-Match Requirements

An approval candidate must have normalized full-name match, position match, school/team match, and
plausible college seasons before the draft year. Nicknames, suffixes, abbreviations, and initials
are review triggers, not approval evidence by themselves.

## Transfer Handling

Transfers require a season-by-season team timeline. A player may match multiple schools only when
the timeline is source-approved and every production row can be assigned to the correct player.

## Conflict Handling

- Same-name conflicts: `NEEDS_REVIEW` or `BLOCKED` until unique identity evidence exists.
- Position mismatch: blocked unless a source-approved position history explains the change.
- School mismatch: blocked unless transfer/team timeline evidence resolves it.
- Class/year timeline mismatch: blocked when CFBD seasons occur after the player entered the NFL.

## Blocked/Needs-Review Logic

- `APPROVE_CANDIDATE` means only "candidate worth human review", not model approval.
- `NEEDS_REVIEW` means plausible but insufficient evidence.
- `BLOCKED` means conflicting or unsafe evidence.

## Why Fuzzy Matching Cannot Approve Identities

Fuzzy name matching can surface candidates, but it cannot prove that a college stat row belongs to
the drafted player. Same-name players, position changes, transfers, junior-college paths, and
timeline conflicts can silently leak wrong production into a model. Therefore fuzzy matching is
candidate-generation only.
