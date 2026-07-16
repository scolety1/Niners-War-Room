# Trust Classification Contract

The classifier applies these ordered rules:

1. Blank and explicit unknown values map to `NOT_ENOUGH_INFORMATION`.
2. Existing canonical negative families retain their distinct mappings:
   identity exception, gated, stale, unavailable, missing, and source exception.
3. Word-bounded lexical negators (`no`, `not`, `never`, `without`) and bounded
   negative status words such as `unmatched` reject positive classification.
4. Only word-bounded positive status tokens or the two existing producer phrases
   (`full dynasty source`, `admitted identifier present`) may map to
   `VALID_CURRENT`.
5. Everything else maps to `NOT_ENOUGH_INFORMATION`.

Hyphens and underscores are separators, so `NOT CURRENT`, `not-current`, and
`not_current` follow the same fail-closed rule. `not available` and
`not currently available` retain the distinct `UNAVAILABLE` state;
field-specific `unmatched` retains `IDENTITY_EXCEPTION`.

The contract does not calculate freshness, source validity, admission, or a new
fact. It classifies existing display text conservatively.
