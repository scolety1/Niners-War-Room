# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is mostly disciplined and mission-fit, but it still needs tighter staging and less internal process language before the app feels like a confident table-first command tool.

## Mission Voice Fit
The language matches the project mission well when it stays close to concrete nouns: official top five, forced release, keeper pressure, pick value, trade board, import review, model audit. That vocabulary fits a private local-first fantasy football decision engine and avoids generic fantasy advice language. The strongest copy protects determinism by saying formulas, source, assumptions, confidence, and local CSV/SQLite snapshots. The weaker copy appears in process-heavy docs and repair language, where terms like "handoff", "workflow", "polish", "ship", "active pack", and "repair lane" are useful internally but should not leak into the working app.

## Delicate Wording Risks
- "Drop Deadline Command Center" is strong as a project name, but it can become inflated if every screen uses command-center language. In the app, prefer concrete page labels and table names.
- "War Room Rank" and "War Score" need careful separation from Official Rank, Market Rank, and My Rank. Any visible copy that blends them could imply the tool is giving one true answer instead of computed model output.
- "Which trade options can save value" risks overclaiming if the app cannot verify acceptance, league politics, or future outcomes. Prefer "show value gaps" or "surface trade candidates for review".
- "Which players are likely to enter the draft pool" should be staged as an estimate or model output, not a prediction. Prefer "projected draft pool" with assumptions visible.
- "Recommendation labels" such as LOCK, DROP, TARGET, FADE, and AVOID are useful but can sound too absolute unless paired with confidence, source, and why.
- "AcceptanceChance" is legally and analytically delicate as a label. It can read like prediction theater. Prefer "acceptance estimate" or "manual review signal" where space allows.
- Internal phrases in task and review docs, including "ready for service", "manager-ready", "polish", "handoff", "workflow", "repair lane", and "ship", should not appear in customer-facing app copy.
- "No Blocking Visual Bugs" is misleading when screenshots show "Not found". That mismatch is a copy trust issue as much as a QA issue.
- "PrivateTradeScore" and "MarketTradeScore" are fine as model fields, but visible labels should be spaced and plain: "Private trade score", "Market trade score".
- The current route failure copy, "Not found", is too bare for a local tool if it appears in the app. It should become a concrete recovery state only after routing is fixed.

## Beautiful Language Opportunities
- Make first-screen labels shorter and more decisive: "Official top five", "Default release", "Keeper pressure", "Pick values", "Model audit".
- Use "computed from" language near formulas to make the tool feel exact without sounding grand.
- Replace advice-like phrasing with review-oriented phrasing: "Review", "flag", "compare", "sort", "audit".
- Give empty and error states useful context: what is missing, which file or route is affected, and what the user can do next.
- Keep long model explanations behind expanders with restrained labels such as "Why this score", "Inputs", "Source rows", and "Assumptions".
- Use "snapshot" consistently for local data packs. It is concrete, quiet, and aligned with the local-first promise.
- Keep the app voice drier than the review docs. The working tool should feel like a decision table, not a launch memo.

## Priority Rewrite
Fix any visible copy that implies the model is making confident fantasy advice rather than recalculating deterministic assumptions from local snapshots. The most important next pass should review table headings, labels, empty states, and recommendation text for advice words like "should", "save", "likely", "target", and "avoid", then add nearby source, confidence, or assumption language where the label could otherwise overpromise.

## Suggested Rewrites
- Before: "Which trade options can save value before Roster Declaration Day?"
  After: "Which trade candidates show a value gap before Roster Declaration Day?"

- Before: "Which players are likely to enter the draft pool?"
  After: "Which players project into the draft pool under current assumptions?"

- Before: "AcceptanceChance"
  After: "Acceptance estimate"

- Before: "No Blocking Visual Bugs"
  After: "Automated visual check found no issues in the captured routes"

- Before: "Not found"
  After: "Page route not found. Open the Streamlit page from the sidebar or check the visual QA route list."

- Before: "Drop candidate score"
  After: "Drop pressure score"

- Before: "Trade options"
  After: "Trade candidates for review"

- Before: "Recommendation"
  After: "Model label"

## Voice Rules
- Use concrete fantasy and data nouns: official rank, market rank, keeper score, pick value, roster slot, source file, snapshot.
- Keep the first screen short: one primary table, compact status, minimal helper text.
- Do not write like a fantasy advice blog. Avoid hype, certainty, and guru phrasing.
- Separate computed output from human decision language.
- Pair strong labels like DROP, AVOID, TARGET, and LOCK with confidence, source, or "why" access.
- Prefer "review", "flag", "compare", and "audit" over "optimize", "win", "save", or "predict".
- Keep internal process words out of visible app copy.
- Use title case sparingly for page names; use sentence case for helper text and table labels.

## Next 5 Copy Tasks
- [ ] Review all Streamlit page titles and table headings; keep labels concrete and under five words where practical.
- [ ] Replace advice-like trade copy with review-oriented language; guardrail: do not change formulas or labels in code outputs unless display-only.
- [ ] Audit recommendation labels for certainty; guardrail: every strong action label must have confidence, source, or "why" nearby.
- [ ] Rewrite route and empty states so they name the missing page, file, or snapshot; guardrail: no broad UX redesign.
- [ ] Move long model explanation copy behind existing expanders or side panels; guardrail: first viewport must remain table-first.

## Stop Or Continue
continue but fix copy first