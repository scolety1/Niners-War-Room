# Deterministic ordering contract

Inputs are first validated against exact tracked hashes, optionally perturbed,
then canonicalized. Governed sort keys include target/input season, fixed
position order `QB, RB, WR, TE`, exact player ID, candidate, and stable row ID.
Ranks use score descending, display name, exact player ID, and row ID, with
nulls last.

All CSV row collections are sorted explicitly before UTF-8/LF serialization.
Floats use six decimal places. JSON keys are sorted. Filesystem inventory is
sorted. Git evidence is anchored to the fixed source commit and sorted.
Manifest self-hashing is excluded.

Original, reversed, and fixed-seed random inputs; tied primary values; null
sort fields; and non-ASCII display metadata reproduce identical governed
outputs.
