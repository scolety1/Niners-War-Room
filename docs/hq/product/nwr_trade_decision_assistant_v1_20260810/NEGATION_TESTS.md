# Negation Tests

Verified failures are prevented for:

- display formatting changing the recommendation;
- ghost keys affecting the decision;
- missing evidence becoming zero;
- rookie ranks entering Finished V1 comparisons;
- picks receiving invented player-equivalent values;
- market totals entering NWR synthesis;
- team window changing base ranks;
- blocked evidence producing a confident recommendation;
- a named counter containing an unowned asset or pick;
- split incoming ownership being guessed as one manager;
- different-market-snapshot values being combined;
- owner/opponent duplicates or side overlap;
- advisory receipt persistence mutating source snapshots.

The exact owner case asserts zero suggested counters under the blocked ownership state.

