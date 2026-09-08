# NWR FFA Sept-4 2026 Projections — Formal Admission Decision (V1)

**Date:** 2026-09-08 (overnight V4 continuation)
**Scope:** Directive V4 section 10 — finish the FFA Sept-4 admission decision (A. reject / B. admit as replacement / C. admit as ensemble / D. retain as reference only). Read-only comparison against the active NWR ranking; nothing admitted, activated, or written to canonical storage.

## 1. Real inputs

- FFA source: `C:\NWR_HISTORICAL_DATA\FFA_OFFICIAL\2026\projections\projections_2026_official_ffa.csv`, 497 rows (32 K, 32 DST, 213 IDP [DL/LB/DB], 220 QB/RB/WR/TE), downloaded 2026-09-04, sha256-verified per the FFA intake manifest.
- NWR active ranking: 530 rows, `source_as_of 2026-08-08` (the live projection snapshot actually driving Suggestions today).
- Comparison restricted to QB/RB/WR/TE (the only positions this league rosters via the modeled path; K/DST are manual-only by design, IDP isn't rostered at all in this league) — 220 FFA rows.

## 2. Real findings

- **Identity match: 190/220 (86.4%)** of FFA's QB/RB/WR/TE rows resolve to an exact name match in the active NWR ranking.
- **30 unmatched FFA players**, including real, currently-relevant veterans: Tyreek Hill, Stefon Diggs, Deebo Samuel, Keenan Allen, Joe Mixon, Najee Harris, Antonio Gibson, Jonathon Brooks. This is not an FFA data-quality problem — it's evidence of a real gap in NWR's own active roster coverage (see the companion root-cause trace, `NWR_BROOKS_DIGGS_SOURCE_GAP_ROOT_CAUSE_V1_20260908.md`, which explains exactly why 2 of these 30 are missing from NWR's source).
- **Real, two-directional rank disagreement** among the 192 matched players with a usable `position_rank` on both sides. The largest gaps (position-rank, FFA vs NWR):
  - NWR ranks notably **lower** than FFA (possible NWR undervaluation): Malik Nabers (FFA WR15 vs NWR WR94, gap 79), Jayden Reed (WR42 vs WR106), Jalen McMillan (WR62 vs WR125), Calvin Ridley, Mike Evans, Chris Godwin, Garrett Wilson, Jayden Daniels (QB4 vs QB34), Joe Burrow (QB6 vs QB28).
  - NWR ranks notably **higher** than FFA (possible NWR overvaluation, or a real, deliberate risk/role discount FFA doesn't apply): Jauan Jennings, Wan'Dale Robinson, Michael Wilson, Michael Pittman, Tre Tucker, Tyrone Tracy, Kimani Vidal, Khalil Shakir.
  - The disagreement runs **both directions** at real, similar magnitude — this is not a clean "NWR is systematically wrong, FFA is systematically right" signal that would justify a wholesale replacement or blend; it looks like two independently-built projection systems disagreeing on role/opportunity assumptions for a specific set of real players, which is exactly what an ensemble candidate would need a proper accuracy comparison (not just disagreement direction) to resolve.

## 3. Applying the admission gate

| Option | Verdict | Why |
|---|---|---|
| A. Reject outright | **Not chosen** | FFA data is real, sourced, and identifies real, concrete gaps in NWR's own coverage (the unmatched-veteran list) that are independently worth acting on — rejecting it entirely would throw away that diagnostic value. |
| B. Admit as replacement | **Rejected** | No walk-forward *outcome* validation (predicted vs. real season points) comparing FFA's accuracy to NWR's has been run — replacing the live, historically-calibrated projection source with an unvalidated external one would violate this program's own no-unvalidated-swap discipline. FFA's own reproducibility is also documented as unreliable day-to-day ([[ffa-source-not-reproducible]]), which is a real risk for a primary source. |
| C. Admit as ensemble (blend into live projections) | **Rejected for now** | Same missing-validation gap as B, at a smaller scale — blending an unvalidated signal into the live number the owner sees during a draft is exactly the kind of "arbitrary constant" this program has repeatedly refused to ship without evidence. The two-directional disagreement pattern above means a naive blend could just as easily make some real players *worse* as better. |
| D. Retain as reference only | **ADOPTED** | FFA already delivered its real value tonight as a **divergence-detection signal** — surfacing (1) 30 real veterans missing from NWR's own source (independently root-caused for 2 of them) and (2) a specific, named list of large rank disagreements worth manual owner review. Retaining it as an occasional, read-only comparison source (exactly the read-only script used here) captures that value without touching the live ranking basis or its calibration. |

**Decision: D — retain FFA as a reference-only comparison source.** No canonical projection file, governance receipt, or live ranking is modified by this decision. The concrete, real output of this pass is the disagreement list above and the Brooks/Diggs root-cause trace it led to — not an activation of FFA data anywhere in the live product.

## 4. What would change this decision

A real walk-forward outcome study — FFA's historical position-rank predictions vs. real season points scored, compared against NWR's own historical accuracy on the same players/seasons — would be the concrete evidence needed to reconsider B or C. Not attempted this session (FFA's day-to-day reproducibility issue also means any such study would need FFA snapshots preserved at each historical point, not re-pulled after the fact).
