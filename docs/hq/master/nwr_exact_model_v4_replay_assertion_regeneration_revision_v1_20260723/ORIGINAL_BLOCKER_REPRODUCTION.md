# Original blocker reproduction

Before hardening, the committed test file reported `8 passed`, but the eight
mutations below survived calls to the production research functions:

1. target-season production substituted for `pyf_prior_nwr_points`;
2. target-season games substituted for `prior_games`;
3. current-only ADP inserted into a historical row;
4. current-board rank inserted as a historical input;
5. a blocked/approximate component relabeled exact without authority;
6. one governed frozen score changed;
7. name-preserving player-ID authority swapped between historical rows;
8. source rows reversed, changing canonical exactness-mask bytes.

The before harness called `exactness_mask`, `baseline_rows`, `load_sources`, and
`age_join`; it did not prove behavior using source substrings or a duplicate
evaluator. Exact fixtures, mutations, functions, outcomes, root causes, and
fail-closed invariants are recorded in `FAILED_MUTATION_RESULTS_BEFORE.csv`.

After hardening, the original eight are 8/8 detected by the production
temporal-record validator, exactness lattice, exact player-ID join, frozen
comparator contract, and canonical ordering layer.
