# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is mostly disciplined and mission-fit, but it still leans on command-center drama and internal process language before the visible product has proven the calm, table-first decision flow.

## Mission Voice Fit
The language matches the product position better than a generic fantasy app would: local-first, deterministic, CSV/SQLite-backed, and built for one owner making drop-deadline decisions. The best copy is concrete: "official top five", "default release", "keeper/drop decisions", "pick values", "trade leverage", and "league pressure." The weaker copy comes from fleet/process artifacts and dramatic labels that can make the app sound more like a codename than a usable analytical tool. For this product, the voice should feel like a private roster desk: terse, sourced, configurable, and careful about the difference between model output and advice.

## Delicate Wording Risks
- "Decision engine" is accurate internally, but customer-facing use can overpromise if the UI does not clearly show assumptions, sources, and formula outputs.
- "Command Center" and "War Room" fit the project identity, but too much of that language can make the product feel theatrical instead of precise.
- "Recommendations" needs care. Use it only when the displayed label is clearly computed from deterministic inputs and supported by a "why" view.
- "Which trade options save value" may imply certainty. Safer phrasing: "which trade options may preserve value under the current model."
- "Which players are likely to enter the draft pool" can sound predictive. Safer phrasing: "which players the model flags as likely draft-pool candidates, with assumptions shown."
- "AcceptanceChance" is risky if presented as a probability rather than a heuristic score. It should be labeled as model output, not a forecast.
- Fleet/process phrases such as "repair active pack", "pause ship", "handoff", "quarantine", "scorecard", and "quality lane" belong in internal docs only, not visible app copy.
- "Magic Improvement Score" is too cute and too vague for an analytical tool. It risks undermining trust in deterministic formulas.
- "No Blocking Visual Bugs" conflicts with the reported "Not found" evidence. That wording is misleading and should be softened or gated by actual route checks.
- "External build passed" is useful in engineering notes, but it should not substitute for user-facing readiness or visual verification.

## Beautiful Language Opportunities
- Replace broad product phrases with concrete table labels: "Official Top Five", "Default Release", "Keeper Pressure", "Pick Value", "Trade Review", "Model Audit."
- Make uncertainty visible in plain language: "Assumptions", "Source", "Formula inputs", "Confidence", "Why this label."
- Use short action labels that match the owner job: "Review drops", "Check top five", "Compare picks", "Open trade board."
- Turn dramatic claims into sober working copy: "Drop Deadline Command Center" can stay as a title, but page subtitles should be practical.
- Use "model flags" or "computed label" when the output is analytical, especially for trade, draft-pool, and pressure language.
- Keep long explanations behind expanders, but give each expander a concrete name such as "Why this score" or "Source rows."
- Separate app copy from fleet copy. The app should sound like a tool for the Niners owner; docs/codex can carry supervisor language.

## Priority Rewrite
The single most important wording problem is analytical certainty around recommendations, trade chance, and draft-pool likelihood. Nami should audit visible labels and subtitles for any phrase that sounds like prediction or advice, then rewrite them as deterministic model outputs with nearby assumptions, source, confidence, and "why" language.

## Suggested Rewrites
- Before: "Which trade options save value before Roster Declaration Day?"
  After: "Which trade options the model says may preserve value before Roster Declaration Day."
- Before: "Which players are likely to enter the draft pool?"
  After: "Which players are flagged as draft-pool candidates under the current assumptions."
- Before: "AcceptanceChance"
  After: "Acceptance Heuristic"
- Before: "recommendations"
  After: "computed labels"
- Before: "Magic Improvement Score"
  After: "Review Score"
- Before: "No Blocking Visual Bugs"
  After: "No blocking visual bugs found in verified screenshots"
- Before: "decision engine"
  After: "local roster decision table"
- Before: "trade options can save value"
  After: "trade options that may reduce keeper-value loss"

## Voice Rules
- Use concrete football and league nouns before brand language.
- Keep page titles short and task-based.
- Treat every score as computed output, not advice.
- Pair uncertain outputs with "assumption", "source", "confidence", or "why."
- Avoid guru language, prediction theater, and one-number certainty.
- Keep internal fleet/process language out of app screens.
- Prefer "flag", "label", "score", "review", and "compare" over "predict", "guarantee", "save", or "optimize."
- Put explanation behind named detail controls, not in first-screen prose.

## Next 5 Copy Tasks
- [ ] Rename any visible "AcceptanceChance" label to "Acceptance Heuristic"; guardrail: do not change formula behavior.
- [ ] Audit visible page subtitles for predictive language like "save value" or "likely"; guardrail: rewrite as model output with assumptions.
- [ ] Replace any visible "recommendation" label that hides formula basis with "computed label" or "model label"; guardrail: keep table columns compact.
- [ ] Remove or rename playful analytical labels such as "Magic Improvement Score" in customer-facing surfaces; guardrail: internal docs may keep process terms if clearly internal.
- [ ] Add one consistent detail label, "Why this score", wherever long formula explanation is hidden; guardrail: do not add new explanatory blocks above the main table.

## Stop Or Continue
continue but fix copy first