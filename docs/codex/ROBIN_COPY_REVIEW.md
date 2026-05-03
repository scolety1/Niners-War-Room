# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is disciplined, local-first, and mission-fit, but too much visible language still sounds like process scaffolding instead of a working drop-deadline command table.

## Mission Voice Fit
The strongest copy fits the project well: "private local-first fantasy football decision engine," "Drop Deadline Command Center," "official top five," "keeper/drop decisions," and "local CSV/SQLite snapshots" all support a serious, deterministic tool for one owner and one league. The voice is not over-polished or salesy, which is right for this product. The main mismatch is staging: visible copy appears to foreground route inspection, build status, and process language when the first screen should answer roster decisions quickly.

## Delicate Wording Risks
- "Inspect route results before any new work continues" is operationally honest but product-hostile if visible to the user.
- "Diagnostic lobby" style copy should not occupy the first screen of the actual app; it tells the owner they are debugging instead of deciding.
- "Command Center" is strong, but risky if the command boards render "Not found" or do not immediately show decision data.
- "War Room Rank," "War Score," and "command board" are acceptable inside this private tool, but should stay attached to concrete table outputs so they do not drift into fantasy-advice theater.
- "Recommendations" can imply advice. Prefer "model labels," "computed labels," or "review flags" where the output is formula-based.
- "Likely to enter the draft pool" should be staged with assumptions and sources; avoid making it sound predictive unless the model basis is visible.
- "Trade options can save value" is a little confident. "Trade options that may preserve value under the current model" is more mathematically honest.
- Repeated process terms such as "repair lane," "handoff," "polish," "ship," "guardrails," and "workflow" belong in docs, not user-facing app surfaces.
- Runtime source paths and route status labels are maintainers' copy, not owner-facing copy.

## Beautiful Language Opportunities
- Make the first screen speak in owner decisions: "Official top five," "Default release," "Keep," "Drop," "Shop," "Pressure," "Pick value."
- Use short table labels with exact meaning instead of explanatory prose.
- Replace process copy with trust copy that names source and timestamp: "Active snapshot," "Loaded rows," "Import warnings," "Model audit."
- Put formula explanations behind "Why" or "Audit" disclosures, not in the primary table.
- Use "computed" and "assumption" language near scenario or model outputs.
- Separate public/product language in README from working app labels in Streamlit.
- Keep "local snapshot" as a trust phrase, but avoid repeating it as a decorative tagline.

## Priority Rewrite
The single most important wording problem is the first-screen shift from decision language to process inspection language. Nami should replace visible route/debug copy with a compact owner-facing command summary: active snapshot, official top five, default release candidate, keeper/drop/shop counts, and links to the real boards. Route checks and source paths should move behind a "System audit" disclosure.

## Suggested Rewrites
- Before: "Inspect route results before any new work continues"
  After: "System audit"

- Before: "Drop Deadline Board"
  After: "Drop deadline"

- Before: "Which trade options save value before Roster Declaration Day?"
  After: "Which trade options may preserve value before Roster Declaration Day?"

- Before: "recommendations"
  After: "computed labels"

- Before: "likely to enter the draft pool"
  After: "projected draft-pool flags"

- Before: "Private, local-first fantasy football decision engine"
  After: "Private local fantasy football decision table"

- Before: "Display deterministic scores and recommendations"
  After: "Display deterministic scores, labels, sources, and assumptions"

## Voice Rules
- Lead with the owner's next decision, not the system's internal process.
- Use concrete nouns: official top five, default release, keeper label, drop label, shop flag, pick value, import warning.
- Keep first-screen labels short; move explanations behind audit or detail panels.
- Use "computed," "source," "assumption," and "why" for model outputs.
- Do not imply prediction, certainty, or expert advice when the system is recalculating deterministic inputs.
- Keep league-specific language; do not broaden into generic fantasy app copy.
- Keep staff/build language out of visible product surfaces unless the user opens system audit.
- Avoid vague value nouns such as "workflow," "polish," "handoff," "artifact," and "solution" in customer-facing copy.

## Next 5 Copy Tasks
- [ ] Replace any visible route-inspection headline with "System audit" or a similarly quiet label; keep route details behind a disclosure.
- [ ] Audit Streamlit page titles and table headers for owner-facing nouns only; remove build/process language from primary screens.
- [ ] Rename visible "recommendation" language to "computed label" where the output comes from formulas; keep "recommendation" only in docs if needed.
- [ ] Add or verify assumption labels near any scenario or projection table; state what changed, what formula uses it, and what remains fixed.
- [ ] Review root-page copy so the first screen answers top five, default release, keeper/drop/shop counts, and active snapshot without explaining the whole system.

## Stop Or Continue
continue but fix copy first