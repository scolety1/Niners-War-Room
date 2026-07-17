# Encoder Algorithm and Idempotence

## Algorithm

1. If the value is not a string, return it unchanged.
2. If the value is the empty string, return it unchanged.
3. If index zero already contains the apostrophe safety marker, return the
   value unchanged.
4. Starting at index zero, advance while the current character belongs to the
   closed five-code-point leading set.
5. Inspect the first remaining character without altering the string.
6. If it is `=`, `+`, `-`, or `@`, return an apostrophe followed by the complete
   original string.
7. Otherwise return the original string unchanged.

The implementation uses an explicit index scan. It does not create a trimmed
or normalized intermediate string.

## Explicit already-protected rule

Any string whose actual index-zero character is the apostrophe marker is
already protected and remains unchanged. This rule is intentionally narrower
than searching for an apostrophe after whitespace.

## Behavioral proof

The focused test matrix asserts `encode(encode(value)) == encode(value)` for
all four formula markers; every individual, repeated, mixed, reverse-mixed,
and bounded-long whitespace prefix; commas; quotes; multiline content;
Unicode; safe values; and already-protected values. The non-idempotent semantic
mutation adds a second marker and is detected. Result: PASS.
