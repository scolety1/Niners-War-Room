# Negated Trust-Status Security Fix

## Outcome

Finding `csf_ee545411ea698019b8df1208` (`CAND-review-004-01`, ledger
`DG001`, occurrence `occ_e6c2696a983ab0eed760f0cb`) is fixed locally.

The protected Decision Trust Strip service now tokenizes status prose into
bounded words, preserves the established negative-state precedence, rejects
lexical negation before positive classification, and recognizes affirmative
tokens only on word boundaries. Negated or contradictory noncanonical text
fails closed and remains visible in the collapsed summary.

No component sink change was necessary: the existing presentation code already
retains source text for every state except `VALID_CURRENT`. Correcting the state
therefore removes the misleading positive substitution without changing page
placement or interaction.

## Authority decision

Canonical downstream state authority is unambiguous: the service already owns
the closed `VALID_CURRENT`, `STALE`, `MISSING`, `GATED`, `UNAVAILABLE`,
`IDENTITY_EXCEPTION`, `SOURCE_EXCEPTION`, and `NOT_ENOUGH_INFORMATION` states.
The imported frozen-board producer is intentionally open-schema, so it cannot
supply a trusted typed state. The authorized fallback is therefore used:
negative-state recognition, lexical-negation rejection, then bounded positive
matching.

## Scope

Only the shared trust classifier and its security regression file changed.
Ordering, page placement, ranking behavior, score behavior, filters, sorting,
freshness thresholds, source admission, provider permissions, and frozen-board
normalization are unchanged.

## Disposition and residual risk

Disposition: `FIXED_LOCAL_ONLY`.

Free-form unknown prose still maps conservatively and may display “Not enough
information.” That is intentional fail-closed behavior, not a factual inference.
The optional branch must not be pushed without separate human review and
authorization.
