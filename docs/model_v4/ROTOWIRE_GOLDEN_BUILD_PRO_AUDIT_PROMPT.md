# Pro Audit Prompt: Model v4 Golden Build

You are auditing a dynasty fantasy football model for a 10-team, 1QB,
non-PPR league with 0.4 points for rushing and receiving first downs.

The model is review-only. Do not treat it as live roster advice. Do not force
the rankings to match public consensus. Your job is to verify whether the model
logic, source handling, receipts, and risk labels are trustworthy enough to
move toward app promotion planning.

## Audit Scope

Please inspect the packet and answer whether the Golden Build is:

- ready for app promotion planning,
- needs formula repair,
- needs source/data repair,
- needs receipt/confidence repair,
- needs architecture repair,
- or is not yet auditable.

## Required Checks

1. Verify whether the model is league-adjusted for:
   - 10-team league depth,
   - 1QB replacement value,
   - non-PPR scoring,
   - no TE premium,
   - 0.4 rushing/receiving first-down scoring,
   - no passing first-down scoring.

2. Verify whether RB/WR/QB/TE balance makes football sense:
   - elite RBs should not be buried by replaceable QBs,
   - elite WRs should remain high unless receipts explain otherwise,
   - QBs should need real 1QB VORP/rushing separation to carry major value,
   - TEs should need a real no-premium VORP gap to justify premium value.

3. Verify whether replacement/VORP logic is correct:
   - replacement baselines are position-specific,
   - VORP is not raw fantasy points,
   - 2025 first-down estimates are clearly labeled `estimated_from_history`,
   - estimated first downs are not represented as direct data.

4. Verify whether route, target, snap, red-zone, alignment, and TE-route
   evidence is labeled honestly:
   - route evidence may be used only from licensed local RotoWire exports,
   - snap share is a role proxy, not route participation,
   - unavailable or missing fields must remain visible.

5. Verify whether missing data is handled safely:
   - missing evidence must not become zero evidence,
   - missing evidence must not become average evidence,
   - confidence should cap or warn; it must not hide uncertainty.

6. Verify whether projections, rankings, ADP, market, and league rank are
   excluded from private football value:
   - they may appear as context only,
   - they must not move Dynasty Asset Value or candidate private value.

7. Verify whether any player ranking is unsupported by receipts. Please pay
   special attention to:
   - Lamar Jackson as a potential sell-high/trade-review case due to
     rushing-age sensitivity in 1QB,
   - Malik Nabers,
   - Brian Thomas Jr.,
   - Luther Burden,
   - De'Von Achane,
   - Bijan Robinson,
   - Jahmyr Gibbs,
   - Brock Bowers,
   - aging veterans such as Christian McCaffrey, Derrick Henry, Keenan Allen,
     Davante Adams, Travis Kelce.

8. Verify whether the app should remain review-only:
   - no active rankings,
   - no My Team decisions,
   - no War Board changes,
   - no roster/draft/final readiness gates should unlock unless the evidence
     truly supports it.

## Output Requested

Produce a triage report with:

- overall verdict,
- issue table with severity,
- affected files,
- affected players or positions,
- evidence,
- likely cause,
- recommended next action,
- suspicious rankings list,
- accepted limitations list,
- exact next patch list.

Be blunt. Do not fake certainty. If a surprising ranking is supported by
receipts, say why. If it is unsupported, identify the file, field, component,
or source gap causing it.
