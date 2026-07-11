# Semantic Consistency and Passive-Adapter Review

## Passive adapter

`src/services/decision_trust_strip_service.py` has no data-source, filesystem, network, registry, identity-service, comparator, or outcome dependency. It accepts a mapping already supplied by a page. It returns immutable dataclasses and does not mutate the input.

The only transformation is documented presentation mapping over explicit existing text. Blank and unrecognized values fail closed to `NOT_ENOUGH_INFORMATION`. Absence of warnings is not treated as current. A date without an explicit freshness state is not declared current.

Distinct trigger vocabularies preserve:

- `VALID_CURRENT`
- `STALE`
- `MISSING`
- `GATED`
- `UNAVAILABLE`
- `IDENTITY_EXCEPTION`
- `SOURCE_EXCEPTION`
- `NOT_ENOUGH_INFORMATION`

Gated is never converted to unavailable; unavailable is never converted to missing; stale remains independent; unresolved identity remains visible. The field order and labels match the source schema and glossary.

## Component

`app/components/decision_trust_strip.py` renders only supplied dataclasses. It performs no lookup and writes no session state. Compact summaries are text and symbol based. Expanded details use `st.expander` and display existing values; they do not copy or invent receipts.

## Surfaces

- Dynasty Rankings adds one dataset-evidence render before existing filters. Existing ranks, row population, presets, filters, sorting and table construction are unchanged.
- Player Compare builds one independent strip from each already selected row. It produces no relative score or better-player recommendation.
- Trading Lab builds one strip from each already selected manual item. It produces no fairness, value adjustment, advice, or offer.

Result: `PASS_PASSIVE_PRESENTATION_ONLY`.
