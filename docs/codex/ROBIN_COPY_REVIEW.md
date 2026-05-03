# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is clear, disciplined, and mission-fit, but some app and review language still leans toward internal command jargon instead of plain analytical product copy.

## Mission Voice Fit
The language mostly matches the mission: private, local-first, deterministic, table-first, and built for one serious fantasy football owner rather than a general advice audience. The strongest copy uses concrete nouns like "official top five", "forced-release risk", "pick value table", "import errors", and "keeper pressure". The weakest copy appears where internal fleet language leaks into the product surface or task language: "war room", "command center", "repair lane", "active work pack", "pause ship", and "No More Features Lock" may be useful internally, but they should stay out of user-facing Streamlit screens unless the audience is explicitly the builder.

## Delicate Wording Risks
- "Decision engine" is acceptable for internal and README copy, but customer-facing analytical UI should not imply the app decides for the owner. Prefer "decision table", "model output", or "roster review tool" where the user is interpreting results.
- "War Room Rank" is mission-specific and probably intentional, but it can blur model output with authority. Pair it with "why", "source", or "assumptions" in detail views.
- "Which players should be kept, dropped, or shopped?" is useful, but "should" can sound advisory. In app copy, prefer "Keep, drop, and shop candidates" or "model labels".
- "Which trade options can save value" risks overclaiming. The app can surface estimated value gaps, not guarantee saved value.
- "Likely to enter the draft pool" should be staged with confidence and assumptions. Without that, it can sound predictive rather than computed.
- "AcceptanceChance" should not read like a true probability unless calibrated. Label it as "acceptance estimate" or "review estimate" if calibration is not proven.
- "POLITICAL RISK" is vivid and useful, but it needs a plain definition in row details so it does not feel cute or arbitrary.
- Internal phrases like "repair lane", "active work pack", "pause ship", "No More Features Lock", "quarantined", and "guardrails failed" belong in Codex docs, not product UI.
- "Command Center" fits the project tone, but the first screen should still lead with the concrete job, not a dramatic product name.

## Beautiful Language Opportunities
- Use "Roster Declaration Day" sparingly as the human deadline anchor; it gives the tool purpose without adding hype.
- Replace advice verbs with evidence nouns: "release risk", "keeper pressure", "value gap", "rank source", "confidence", "assumption".
- Make table headers short and exact: "Official Rank", "Market Rank", "War Room Rank", "My Rank", "Keeper", "Drop Risk", "Trade Fit", "Confidence".
- Give model details a calm audit voice: "Why this label", "Inputs used", "Assumptions", "What changed", "Source".
- Use empty states that sound useful, not decorative: "No import errors found" and "Load a local data pack to review roster pressure."
- Keep page descriptions functional and one-line. The app should feel like an operating table, not a fantasy column.

## Priority Rewrite
The single most important wording problem is analytical certainty. Any phrase that says or implies the model knows what a user "should" do, what trades "save value", or what players are "likely" to do should be rewritten as computed output with visible assumptions, sources, and confidence. Nami should prioritize UI labels and page subtitles before docs polish.

## Suggested Rewrites
- Before: "Which players should be kept, dropped, or shopped?"
  After: "Keep, drop, and shop candidates from the current model run."

- Before: "Which trade options can save value before Roster Declaration Day?"
  After: "Trade ideas with estimated value gap before Roster Declaration Day."

- Before: "Which players are likely to enter the draft pool?"
  After: "Projected draft-pool candidates based on current keeper pressure."

- Before: "AcceptanceChance"
  After: "Acceptance Estimate"

- Before: "Drop Deadline Command Center"
  After: "Drop Deadline Board"

- Before: "V1 is deterministic and explainable."
  After: "V1 uses deterministic formulas with visible inputs and assumptions."

- Before: "Do not use generated AI text to make decisions."
  After: "Model decisions must come from formulas, not generated text."

- Before: "War Score"
  After: "War Room Score"

## Voice Rules
- Use concrete football and league nouns before product metaphors.
- Keep visible app copy short, table-first, and action-specific.
- Separate model output from human advice with labels like "candidate", "estimate", "source", "assumption", and "confidence".
- Do not use fantasy-blog language, hype, prediction theater, or guru phrasing.
- Keep internal fleet terms out of the app surface.
- Put long explanations behind expanders, row details, or audit views.
- Use "should" only in docs or questions, not as a model command in the working app.
- Preserve the distinction between Official Rank, Market Rank, War Room Rank, and My Rank in every visible ranking context.

## Next 5 Copy Tasks
- [ ] Audit Streamlit page titles and subtitles for advice language; guardrail: replace "should" and "save value" with computed-output phrasing.
- [ ] Rename any visible "AcceptanceChance" label to "Acceptance Estimate"; guardrail: do not change formulas or tests.
- [ ] Add or tighten one-line detail labels for confidence and assumptions in Model Audit; guardrail: keep detail behind existing expanders or tables.
- [ ] Review trade board labels for certainty creep; guardrail: preserve OFFER, CONSIDER, HOLD, DECLINE, AVOID, and POLITICAL RISK as deterministic labels.
- [ ] Remove internal fleet wording from any user-facing app strings; guardrail: docs for Codex operations may keep operational terms.

## Stop Or Continue
continue but fix copy first