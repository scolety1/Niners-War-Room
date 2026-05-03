# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is disciplined, local-first, and mission-fit, but several visible labels and review notes still need sharper staging so the product reads as a deterministic command table, not a broad advice dashboard or repair log.

## Mission Voice Fit
The language mostly matches the mission: private, local-first, table-first, deterministic, and built for one Niners co-owner making keeper and drop-deadline decisions. The strongest copy uses concrete nouns such as "official top five", "default release", "keeper pressure", "pick value", and "import errors." The weaker copy appears in system and review language, where phrases like "command center", "war board", "league intel", "model audit", and "trade leverage" can sound useful but still need visible definitions, source labels, and assumption staging inside the app.

## Delicate Wording Risks
- "Decision engine" is acceptable internally, but customer-facing use should not imply the app decides for the owner. Prefer "decision table" or "decision support tool" where the action remains human.
- "Recommendations" can overclaim if shown without nearby source, confidence, and why fields. In analytical software, use "model label" or "computed label" when the output is formula-derived.
- "Which trade options can save value" implies outcome certainty. Better: "Which trade ideas may preserve value under the current assumptions."
- "Which players are likely to enter the draft pool" risks prediction theater unless the page shows assumptions and source inputs. Better: "Projected draft-pool candidates."
- "Trade leverage" can sound salesy or strategic beyond the model. Prefer "trade value gap", "keeper impact", or "opponent benefit."
- "War Room Rank" is on-brand for the project, but it must remain visually separate from Official Rank, Market Rank, and My Rank so it does not look like a hidden truth score.
- "AcceptanceChance" is risky if it reads like a real probability. It should be framed as a heuristic score, not a forecast.
- "Not found" appearing in captured product routes is a copy failure as well as a design failure: it gives the user no destination, recovery action, or concrete explanation.
- Repair-loop language such as "repair active pack before fresh work", "No More Features Lock", "LOOPING_QUALITY", and "smallest blocker-clearing repair" belongs in internal docs only, never in the app.
- "Command Center" is acceptable as a product frame, but the first screen should still lead with the concrete job: official top five, forced release, keep/drop/shop, or import review.

## Beautiful Language Opportunities
- Replace broad command language with precise table titles: "Official Top Five", "Forced Release", "Keep Drop Shop", "Pick Value Curve", "Keeper Pressure."
- Add plain assumption labels near analytical outputs: "Source", "Formula", "Confidence", "Why", and "Assumptions."
- Make empty and error states useful: route failures should tell the user which page failed and how to return to the app root.
- Use restrained football-specific language only where it clarifies the league decision, not as decoration.
- Keep first-screen copy sparse: title, current data pack, import status, and the primary table should do most of the work.
- Convert "recommendation" headings to "Model Label" or "Computed Label" where the app is showing deterministic formula output.
- Make trade copy calmer and more auditable by naming the components: private value, market value, keeper impact, opponent benefit, acceptance heuristic.
- Put long formula explanations behind expanders labeled "Why this label" or "Formula inputs."

## Priority Rewrite
The single most important wording problem is the analytical certainty around model outputs. Nami should audit visible labels that say or imply "recommendation", "likely", "chance", "save value", or "should", then rewrite them as computed, assumption-bound outputs with nearby source and confidence labels. The goal is not softer prose; it is clearer ownership of uncertainty.

## Suggested Rewrites
- Before: "Which trade options can save value before Roster Declaration Day?"
  After: "Which trade ideas may preserve value before Roster Declaration Day under the current assumptions?"

- Before: "Which players are likely to enter the draft pool?"
  After: "Which players project into the draft pool from current keeper pressure?"

- Before: "AcceptanceChance"
  After: "Acceptance Heuristic"

- Before: "recommendations"
  After: "computed labels"

- Before: "Trade leverage"
  After: "Trade value gap"

- Before: "Not found"
  After: "Page not available. Return to the War Room home page and choose a board from the sidebar."

- Before: "V1 is the Drop Deadline Command Center."
  After: "V1 is a local drop-deadline table for top-five release, keeper, trade, and pick-value decisions."

## Voice Rules
- Keep app labels short, concrete, and table-native.
- Use "computed", "model", "source", "confidence", "assumption", and "why" for analytical outputs.
- Do not write as if the app knows the future or is giving fantasy advice.
- Separate league-rule truth from private model opinion at every rank and label.
- Prefer "candidate", "label", "pressure", "gap", and "projection" over "prediction", "best", "smart", "winning", or "must."
- Keep internal repair, guardrail, and build-loop language out of customer-facing screens.
- Put explanations behind expanders or side panels; keep first-screen copy sparse.
- Use football terms only when they clarify the roster decision.

## Next 5 Copy Tasks
- [ ] Rename any visible "recommendation" column or heading to "Computed Label" or "Model Label"; guardrail: do not change formula behavior.
- [ ] Add or verify nearby "Source", "Confidence", and "Why" labels for keeper/drop/shop outputs; guardrail: keep explanations behind existing expanders.
- [ ] Rewrite trade page copy that uses "chance", "save value", or "leverage" so it reads as heuristic and assumption-bound; guardrail: no new features.
- [ ] Replace any visible "Not found" route copy with a useful page-unavailable message and return action; guardrail: do not redesign navigation.
- [ ] Review first-screen headings on each Streamlit page and reduce them to concrete board names; guardrail: no marketing prose above the primary table.

## Stop Or Continue
continue but fix copy first