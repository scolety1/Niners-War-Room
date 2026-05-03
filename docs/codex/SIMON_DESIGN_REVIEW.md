# Simon Design Review

## Verdict
RED

## One-Sentence Read
The branch is dressed like a command center, but the actual command tables are missing from the inspected routes, so right now this is a diagnostic lobby wearing the product's jacket.

## Mission Fit
The root page gestures toward the mission with a local snapshot posture, a sober table, and an inspection workflow. That part is directionally right for a local-first fantasy decision engine. The problem is fatal: the V1 mission is table-first decision support, and the latest route screenshots for Draft Room, Import Review, League Intel, Model Audit, Team, Trade Central, and War Board show "Not found" instead of working boards. A command center cannot be judged as useful when its command screens do not render.

## Taste Check
The visual tone is restrained, readable, and not trapped in generic glossy SaaS nonsense, which is welcome. The typography has enough authority, the red accent feels project-specific, and the table-first root is closer to the mission than a dashboard full of decorative cards.

What is off: the hierarchy is now pointed at process inspection instead of the user's actual drop-deadline job. The homepage says "Inspect route results before any new work continues," which is operationally honest but product-hostile. On mobile, the table overflows horizontally and code-path chips dominate the composition. The big root headline is confident, but confidence without working routes is theater.

## Visual Problems To Fix
- Customer-facing product routes are missing: inspected board routes render "Not found" instead of command tables, which blocks the primary V1 experience.
- The root page is a diagnostic wrapper, not the Drop Deadline Command Center; it centers inspection status rather than "who to keep, drop, shop, or release."
- The first screen repeats product identity without delivering the product: "Local Snapshot Tool" plus "Drop Deadline Board" plus inspection copy creates a wrapper band before any real decision data.
- Route chrome is too loud relative to the job; the red "Inspect route results" button is the strongest object on the page, but it is not the core fantasy decision action.
- The root table prioritizes runtime source paths, which are useful for maintainers but visually wrong for the product's first screen.
- Mobile layout is not acceptable: the runtime source column clips off-screen and turns a simple table into a sideways scroll problem.
- The visible table only lists three boards, while the app has more pages; this makes the product feel incomplete even before the route failures.
- The collapsed "Why this page exists" affordance is fine in principle, but it currently sits under a process page, not behind a useful working board.
- There is no visible forced top-5 release answer, keeper/drop pressure, trade save path, or pick value surface on the first screen.
- Automated visual bug reporting says no blocking bugs, but the screenshots themselves show mission-breaking route failure; the robot missed the point, naturally.

## Strongest Opportunities
- Make the root screen a compact command board with the Niners top-five release status, keeper/drop/shop counts, trade rescue candidates, and data snapshot health visible above the fold.
- Move route inspection, runtime paths, and process explanation behind a quiet "System audit" or "Route checks" detail panel.
- Restore every board route first, then judge visual hierarchy; broken pages make taste work premature.
- Use dense, sortable tables as the hero surface, with small confidence/source badges rather than narrative panels.
- Tighten mobile into stacked table summaries or priority columns instead of letting code paths blow out the viewport.
- Keep the restrained palette and typography, but make red mean urgency or forced release risk, not generic navigation emphasis.
- Treat Model Audit as an internal trust layer, not a first-class peer to player decision boards unless the user intentionally opens it.

## Priority Fix
Restore the actual Streamlit board routes and make the first rendered screen a working command table, not a route-inspection landing page. The next task should remove "Not found" from all inspected product routes and ensure the root page immediately shows at least the top-five release answer, import/data snapshot status, and links into the real boards with quiet secondary chrome. No new features, no decorative redesign, no bigger dashboard. Make the existing product visible.

## Magic Improvement Score
SCORE: 1; DIRECTION: regressed; ACTIVE_PACK: none; REASON: route screenshots still show missing command tables and the root is a diagnostic wrapper instead of the V1 product.

## Designer Handoff
Next implementer: keep the austere table-first language, the local snapshot tone, and the low-text discipline. Change the hierarchy so the user's deadline decision is first and the build/process inspection is secondary. The top of the app should feel like a war-room work surface: current snapshot, official top five, forced release candidate, keeper pressure, and board navigation. Hide runtime source paths and "why this exists" copy behind a system/audit control. The result should feel like the owner can make a drop decision in 30 seconds, not like they are being invited to debug the app.

## What Not To Do Next
- Do not add more sections to the root page while routes are missing.
- Do not make a prettier diagnostic page and call it product progress.
- Do not add charts, prediction cards, or strategy theatrics before the command tables render.
- Do not expand copy to explain the model on the first screen.
- Do not let runtime file paths compete with player, roster, rank, and pick data.
- Do not treat the automated "No Blocking Visual Bugs" report as design clearance.
- Do not ignore mobile; the current root table already shows horizontal failure.
- Do not touch backend scope, package setup, auth, deployment, or analytics to solve a visual route problem.

## Next 5 Design Tasks
- [ ] Restore all inspected board routes so Draft Room, Import Review, League Intel, Model Audit, Team, Trade Central, and War Board render product content, with no "Not found" screenshots accepted.
- [ ] Replace the root diagnostic-first layout with a compact command summary showing snapshot status, top-five release candidate, keeper/drop/shop counts, and primary board links; keep explanations collapsed.
- [ ] Move runtime source paths and route inspection details into a quiet secondary "System audit" disclosure; do not show code paths in the main first-screen table.
- [ ] Rework mobile root tables to show priority columns only, with no clipped code chips or horizontal overflow in a 390px-wide screenshot.
- [ ] Re-run visual inspection after the route repair and capture root plus at least Import Review, Team, War Board, Draft Room, and League Intel on desktop and mobile.

## Stop Or Continue
stop for human design review