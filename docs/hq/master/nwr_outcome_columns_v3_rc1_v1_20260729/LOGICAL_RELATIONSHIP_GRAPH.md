# Logical relationship graph

The governed graph contains 108 partial-order edges.
For every player, threshold nesting requires narrower thresholds to be no more
probable than broader thresholds. Every exact-year probability and the
two-of-three probability must be no greater than Within 3 Years; Within 3 Years
must be no greater than Within 5 Years. No order is imposed among exact years.

A deterministic upward closure projects only broader events. Raw violations,
governed violations, and per-field adjustment burden are reported separately.
Calibrator selection occurs only after the preregistered projection-burden gate.

| narrower_field | broader_field | relationship | authority |
| --- | --- | --- | --- |
| QB_T12_NEXT_YEAR | QB_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| QB_T12_THIS_YEAR | QB_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| QB_T12_TWO_OF_NEXT_3Y | QB_T12_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| QB_T12_T_PLUS_2 | QB_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| QB_T12_WITHIN_3Y | QB_T12_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| QB_T6_NEXT_YEAR | QB_T12_NEXT_YEAR | probability_lte | threshold event-set nesting |
| QB_T6_NEXT_YEAR | QB_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| QB_T6_THIS_YEAR | QB_T12_THIS_YEAR | probability_lte | threshold event-set nesting |
| QB_T6_THIS_YEAR | QB_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| QB_T6_TWO_OF_NEXT_3Y | QB_T12_TWO_OF_NEXT_3Y | probability_lte | threshold event-set nesting |
| QB_T6_TWO_OF_NEXT_3Y | QB_T6_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| QB_T6_T_PLUS_2 | QB_T12_T_PLUS_2 | probability_lte | threshold event-set nesting |
| QB_T6_T_PLUS_2 | QB_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| QB_T6_WITHIN_3Y | QB_T12_WITHIN_3Y | probability_lte | threshold event-set nesting |
| QB_T6_WITHIN_3Y | QB_T6_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| QB_T6_WITHIN_5Y | QB_T12_WITHIN_5Y | probability_lte | threshold event-set nesting |
| RB_T12_NEXT_YEAR | RB_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T12_NEXT_YEAR | RB_T24_NEXT_YEAR | probability_lte | threshold event-set nesting |
| RB_T12_THIS_YEAR | RB_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T12_THIS_YEAR | RB_T24_THIS_YEAR | probability_lte | threshold event-set nesting |
| RB_T12_TWO_OF_NEXT_3Y | RB_T12_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| RB_T12_TWO_OF_NEXT_3Y | RB_T24_TWO_OF_NEXT_3Y | probability_lte | threshold event-set nesting |
| RB_T12_T_PLUS_2 | RB_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T12_T_PLUS_2 | RB_T24_T_PLUS_2 | probability_lte | threshold event-set nesting |
| RB_T12_WITHIN_3Y | RB_T12_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| RB_T12_WITHIN_3Y | RB_T24_WITHIN_3Y | probability_lte | threshold event-set nesting |
| RB_T12_WITHIN_5Y | RB_T24_WITHIN_5Y | probability_lte | threshold event-set nesting |
| RB_T24_NEXT_YEAR | RB_T24_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T24_NEXT_YEAR | RB_T36_NEXT_YEAR | probability_lte | threshold event-set nesting |
| RB_T24_THIS_YEAR | RB_T24_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T24_THIS_YEAR | RB_T36_THIS_YEAR | probability_lte | threshold event-set nesting |
| RB_T24_TWO_OF_NEXT_3Y | RB_T24_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| RB_T24_TWO_OF_NEXT_3Y | RB_T36_TWO_OF_NEXT_3Y | probability_lte | threshold event-set nesting |
| RB_T24_T_PLUS_2 | RB_T24_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T24_T_PLUS_2 | RB_T36_T_PLUS_2 | probability_lte | threshold event-set nesting |
| RB_T24_WITHIN_3Y | RB_T24_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| RB_T24_WITHIN_3Y | RB_T36_WITHIN_3Y | probability_lte | threshold event-set nesting |
| RB_T24_WITHIN_5Y | RB_T36_WITHIN_5Y | probability_lte | threshold event-set nesting |
| RB_T36_NEXT_YEAR | RB_T36_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T36_THIS_YEAR | RB_T36_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T36_TWO_OF_NEXT_3Y | RB_T36_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| RB_T36_T_PLUS_2 | RB_T36_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T36_WITHIN_3Y | RB_T36_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| RB_T6_NEXT_YEAR | RB_T12_NEXT_YEAR | probability_lte | threshold event-set nesting |
| RB_T6_NEXT_YEAR | RB_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T6_THIS_YEAR | RB_T12_THIS_YEAR | probability_lte | threshold event-set nesting |
| RB_T6_THIS_YEAR | RB_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T6_TWO_OF_NEXT_3Y | RB_T12_TWO_OF_NEXT_3Y | probability_lte | threshold event-set nesting |
| RB_T6_TWO_OF_NEXT_3Y | RB_T6_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| RB_T6_T_PLUS_2 | RB_T12_T_PLUS_2 | probability_lte | threshold event-set nesting |
| RB_T6_T_PLUS_2 | RB_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| RB_T6_WITHIN_3Y | RB_T12_WITHIN_3Y | probability_lte | threshold event-set nesting |
| RB_T6_WITHIN_3Y | RB_T6_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| RB_T6_WITHIN_5Y | RB_T12_WITHIN_5Y | probability_lte | threshold event-set nesting |
| TE_T12_NEXT_YEAR | TE_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| TE_T12_THIS_YEAR | TE_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| TE_T12_TWO_OF_NEXT_3Y | TE_T12_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| TE_T12_T_PLUS_2 | TE_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| TE_T12_WITHIN_3Y | TE_T12_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| TE_T6_NEXT_YEAR | TE_T12_NEXT_YEAR | probability_lte | threshold event-set nesting |
| TE_T6_NEXT_YEAR | TE_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| TE_T6_THIS_YEAR | TE_T12_THIS_YEAR | probability_lte | threshold event-set nesting |
| TE_T6_THIS_YEAR | TE_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| TE_T6_TWO_OF_NEXT_3Y | TE_T12_TWO_OF_NEXT_3Y | probability_lte | threshold event-set nesting |
| TE_T6_TWO_OF_NEXT_3Y | TE_T6_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| TE_T6_T_PLUS_2 | TE_T12_T_PLUS_2 | probability_lte | threshold event-set nesting |
| TE_T6_T_PLUS_2 | TE_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| TE_T6_WITHIN_3Y | TE_T12_WITHIN_3Y | probability_lte | threshold event-set nesting |
| TE_T6_WITHIN_3Y | TE_T6_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| TE_T6_WITHIN_5Y | TE_T12_WITHIN_5Y | probability_lte | threshold event-set nesting |
| WR_T12_NEXT_YEAR | WR_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T12_NEXT_YEAR | WR_T24_NEXT_YEAR | probability_lte | threshold event-set nesting |
| WR_T12_THIS_YEAR | WR_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T12_THIS_YEAR | WR_T24_THIS_YEAR | probability_lte | threshold event-set nesting |
| WR_T12_TWO_OF_NEXT_3Y | WR_T12_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| WR_T12_TWO_OF_NEXT_3Y | WR_T24_TWO_OF_NEXT_3Y | probability_lte | threshold event-set nesting |
| WR_T12_T_PLUS_2 | WR_T12_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T12_T_PLUS_2 | WR_T24_T_PLUS_2 | probability_lte | threshold event-set nesting |
| WR_T12_WITHIN_3Y | WR_T12_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| WR_T12_WITHIN_3Y | WR_T24_WITHIN_3Y | probability_lte | threshold event-set nesting |
| WR_T12_WITHIN_5Y | WR_T24_WITHIN_5Y | probability_lte | threshold event-set nesting |
| WR_T24_NEXT_YEAR | WR_T24_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T24_NEXT_YEAR | WR_T36_NEXT_YEAR | probability_lte | threshold event-set nesting |
| WR_T24_THIS_YEAR | WR_T24_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T24_THIS_YEAR | WR_T36_THIS_YEAR | probability_lte | threshold event-set nesting |
| WR_T24_TWO_OF_NEXT_3Y | WR_T24_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| WR_T24_TWO_OF_NEXT_3Y | WR_T36_TWO_OF_NEXT_3Y | probability_lte | threshold event-set nesting |
| WR_T24_T_PLUS_2 | WR_T24_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T24_T_PLUS_2 | WR_T36_T_PLUS_2 | probability_lte | threshold event-set nesting |
| WR_T24_WITHIN_3Y | WR_T24_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| WR_T24_WITHIN_3Y | WR_T36_WITHIN_3Y | probability_lte | threshold event-set nesting |
| WR_T24_WITHIN_5Y | WR_T36_WITHIN_5Y | probability_lte | threshold event-set nesting |
| WR_T36_NEXT_YEAR | WR_T36_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T36_THIS_YEAR | WR_T36_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T36_TWO_OF_NEXT_3Y | WR_T36_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| WR_T36_T_PLUS_2 | WR_T36_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T36_WITHIN_3Y | WR_T36_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| WR_T6_NEXT_YEAR | WR_T12_NEXT_YEAR | probability_lte | threshold event-set nesting |
| WR_T6_NEXT_YEAR | WR_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T6_THIS_YEAR | WR_T12_THIS_YEAR | probability_lte | threshold event-set nesting |
| WR_T6_THIS_YEAR | WR_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T6_TWO_OF_NEXT_3Y | WR_T12_TWO_OF_NEXT_3Y | probability_lte | threshold event-set nesting |
| WR_T6_TWO_OF_NEXT_3Y | WR_T6_WITHIN_3Y | probability_lte | two qualifying seasons implies at least one |
| WR_T6_T_PLUS_2 | WR_T12_T_PLUS_2 | probability_lte | threshold event-set nesting |
| WR_T6_T_PLUS_2 | WR_T6_WITHIN_3Y | probability_lte | exact-year event subset of three-year cumulative event |
| WR_T6_WITHIN_3Y | WR_T12_WITHIN_3Y | probability_lte | threshold event-set nesting |
| WR_T6_WITHIN_3Y | WR_T6_WITHIN_5Y | probability_lte | three-year cumulative event subset of five-year event |
| WR_T6_WITHIN_5Y | WR_T12_WITHIN_5Y | probability_lte | threshold event-set nesting |
