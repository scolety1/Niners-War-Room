# Trading Lab Safe Rewrite Library

Date: 2026-06-18

## Purpose

This library helps convert unsafe or prohibited wording into research-only,
paper-only language. It is not investment advice.

| unsafe wording | safe rewrite | expected validation |
| --- | --- | --- |
| Buy now | Research whether the public evidence still supports the paper thesis. | Unsafe rejected; rewrite accepted |
| Sell now | Review downside evidence and invalidation notes. | Unsafe rejected; rewrite accepted |
| Place order | Add a paper-only hypothetical note for manual review. | Unsafe rejected; rewrite accepted |
| Use broker token | Prohibited; remove credential reference completely. | Unsafe rejected |
| Based on my account balance | Use hypothetical paper sizing assumptions without private data. | Unsafe rejected; rewrite accepted |
| Auto execute if | Use a manual review trigger for a hypothetical paper scenario. | Unsafe rejected; rewrite accepted |
| Guaranteed return | Frame uncertainty, risks, and invalidation conditions. | Unsafe rejected; rewrite accepted |

## Safe Language Pattern

- Ask a research question.
- Cite public/manual sources.
- Name risks and assumptions.
- Define invalidation conditions.
- Keep the artifact paper-only and manual-review-only.

## Prohibited Language Pattern

- Commands to buy, sell, place, submit, or execute.
- Broker/API/credential/secret references.
- Private account or balance references.
- Guaranteed return claims.
- Automated execution or trigger wording.
