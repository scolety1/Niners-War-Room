# Validation Results

## Final verdict

`GREEN_FANTASY_PLUGIN_RESEARCH_SANITIZED_AND_CLOSED_MANUAL_ONLY`

## Repository and history

| Check | Result |
| --- | --- |
| Fetch all remotes | PASS |
| Live HQ verification at lane start | PASS — `5c04f8aeca6269c71778bc3ca0b94591efd8797c` |
| Remote advance at lane start | PASS — none |
| Source ancestry | PASS — source parent exactly equals verified HQ base |
| Source ahead/behind | PASS — `1` ahead and `0` behind |
| Source common Git directory | PASS — shared with canonical repository |
| Source worktree cleanliness | PASS |
| Remote branches containing private source commit | PASS — `0` |
| Source merged or cherry-picked | PASS — no |

## Artifact structure

| Check | Result |
| --- | --- |
| Required file inventory | PASS — 18 of 18 |
| CSV parsing | PASS |
| Duplicate keys | PASS — none |
| Manifest schema and file coverage | PASS |
| Manifest SHA-256 verification | PASS |
| Staged-path allowlist | PASS |

## Privacy, output, and rights

| Check | Result |
| --- | --- |
| Known private-value scan | PASS — no matches |
| Identifier, email, token, credential, cookie, and authorization pattern scan | PASS — no prohibited values |
| Restricted receipt absence | PASS — no receipt file or directory staged |
| Raw private plugin response absence | PASS |
| Local receipt-path absence | PASS |
| Provider-output quotation review | PASS — aggregate paraphrases only |
| Unknown downstream rights preserved as blocker | PASS |

## Governance consistency

| Check | Result |
| --- | --- |
| No-recreate consistency | PASS |
| Manual-only classifications consistent | PASS |
| External influence consistently 0 percent | PASS |
| Adapter and disagreement panel consistently blocked | PASS |
| Reentry triggers present | PASS |
| Rookie Evidence Workspace not started | PASS |

## Scope and Git hygiene

| Check | Result |
| --- | --- |
| Protected-path scan | PASS — no protected path changed |
| Frozen-artifact scan | PASS — no immutable 2026 artifact changed |
| App/ranking/formula/source-registry diff scan | PASS — no changes |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Final remote lease check before push | PASS |
| Normal non-force push | PASS |
| Clean worktree after commit and push | PASS |
