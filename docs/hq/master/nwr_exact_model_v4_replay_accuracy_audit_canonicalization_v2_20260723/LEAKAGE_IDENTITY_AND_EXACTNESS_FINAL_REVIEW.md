# Leakage, identity, and exactness final review

Temporal assertions now require explicit historical admissibility metadata and
reject all eight temporal mutations. Identity assertions require governed
player IDs and reject all seven identity mutations. The exactness lattice
rejects all six exactness mutations and derives completeness across every
mandatory component.

Adoption reran these boundaries through the focused 32-test suite as part of
the full 2,798-test Hermetic verification. No test-only evaluator or
source-substring proof was accepted. No new skip, xfail, or xpass was added.

Final results:

- temporal mutations: 8/8 detected;
- identity mutations: 7/7 detected;
- exactness mutations: 6/6 detected;
- exact replay remains 0/5,518 rows;
- proxy evidence remains proxy evidence; and
- no name fallback, invented identity, current-only input, or future evidence
  was admitted.
