# Original audit findings

Before correction, static placeholders did not execute universal-age,
productive-veteran-guard removal, low-games-guard removal, swapped lens-value,
or swapped Team Window source defects. Unsupported-rookie injection was
detectable, but the normal zero-rookie current board made that assertion
vacuous. The replacement harness records this in `before_observed` and now
executes all mutations.

The original second-year display contained 40 of 43 mechanically qualifying
players due to `.head(40)`. The omitted rows were LeQuint Allen, Jaydon Blue,
and Kaleb Johnson. Regeneration contains all 43:
Ashton Jeanty, Bhayshul Tuten, Brashard Smith, Cam Skattebo, Cam Ward, Chimere Dike, Colston Loveland, Devin Neal, Dont'e Thornton, Dylan Sampson, Elic Ayomanor, Elijah Arroyo, Emeka Egbuka, Gunnar Helm, Harold Fannin, Isaac TeSlaa, Isaiah Bond, Jacory Croskey-Merritt, Jaxson Dart, Jayden Higgins, Jaydon Blue, Jaylin Noel, Kaleb Johnson, Kyle Monangai, LeQuint Allen, Luther Burden, Mason Taylor, Matthew Golden, Ollie Gordon, Omarion Hampton, Oronde Gadsden, Pat Bryant, Quinshon Judkins, RJ Harvey, Savion Williams, Shedeur Sanders, Tetairoa McMillan, Tory Horton, Travis Hunter, Tre' Harris, TreVeyon Henderson, Tyler Warren, Woody Marks.

The original availability result reused predicted games fraction both as a
continuous expectation and as if it were `P(games >= 8)`. MAE could describe
the continuous expectation, but its Brier, binary log loss, and binary ECE
claims were semantically invalid. The original combined diagnostics were Brier
0.175790941, MAE 0.216979596, log loss 0.553593670, and ECE 0.067893976.

The prior evaluator pooled all seasons before nDCG. The corrected tables keep
that pooled value only in explicitly named diagnostic columns and make
season-level aggregation primary. The original changed-file inventory also
omitted `.gitattributes`; the regenerated inventory is mechanically derived.
