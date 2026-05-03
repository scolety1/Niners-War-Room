# Robin Copy Review

## Verdict
YELLOW

## One-Sentence Read
The voice is mostly disciplined and mission-fit, but too much visible language still reads like QA machinery instead of a private decision instrument for the Niners owner.

## Mission Voice Fit
The strongest copy matches the mission well: "private local-first fantasy football decision engine," "Drop Deadline Command Center," "official top five," "default release," "keeper pressure," and "pick value" are concrete, useful, and specific to the product. The voice is appropriately restrained for analytical software and does not drift into fantasy-advice hype. The weak spot is staging: root and review language such as "Inspect route results," "visual evidence," "repair lane," "active work pack," and "pause ship and inspect results" belongs in internal QA notes, not in the first impression of the product.

## Delicate Wording Risks
- "Drop Deadline Command Center" is strong as an internal/product name, but if it is the first visible phrase, it should be paired quickly with the concrete job: "Who to keep, drop, or shop."
- "War Room Rank" and "War Score" are evocative, but they need consistent meaning. Do not let them become a catch-all score that hides formula source or uncertainty.
- "recommendations" can imply advice rather than computed output. Prefer "model labels," "score output," or "review flags" near analytical tables.
- "Which trade options save value" risks overclaiming. The model can estimate value impact; it cannot know a trade will save value.
- "players are likely to enter the draft pool" should be staged as a model estimate or rule-derived projection, not certainty.
- "Inspect route results" is customer-facing QA language. It tells the builder what to inspect instead of telling the owner what decision surface is available.
- "ready," "evidence," "recovery," "repair," "handoff," "workflow," "active pack," and "visual route rendering" are fine in docs, but should not appear in the product UI unless explicitly inside an audit/developer panel.
- "AI text" in MODEL_SPEC is useful internally, but public/app copy should avoid positioning the app against AI unless the user needs that trust explanation.
- "command board" is acceptable, but repeated too often it may sound like product theater. Use table labels first: "Roster," "War Board," "Trade Central," "Draft Room," "League Intel," "Model Audit."
- "No Blocking Visual Bugs" conflicts with reported "Not found" route captures. That copy creates false comfort and should be qualified or suppressed when route checks fail.

## Beautiful Language Opportunities
- The first screen can become clearer with a short, direct line: "Review the Niners top five, release pressure, keeper labels, trade leverage, and pick values from the active local snapshot."
- Table headings can carry the product promise without prose: "Official Top Five," "Default Release," "Keep / Drop / Shop," "Trade Leverage," "Keeper Pressure," "Pick Value."
- Empty states should be plain and useful: "No active data pack loaded" or "Run import review before scoring."
- Audit copy can become more trustworthy by using "source," "assumption," "formula," "confidence," and "last snapshot" instead of broad phrases like "model insight."
- Trade copy should separate computed value from human judgment: "Model edge," "Opponent benefit," "Acceptance estimate," and "Manual review required."
- The route failure language should become product-safe: "Page unavailable in this capture" in QA docs, never "Not found" as accepted visual evidence.

## Priority Rewrite
Fix the first-screen and route-evidence language so the product opens on the owner's decision, not the harness. The next copy pass should replace QA-forward labels like "Inspect route results" with owner-facing labels such as "Open War Board" or "Review drop deadline board," and move route status, capture notes, and repair language behind an audit or QA disclosure.

## Suggested Rewrites
- Before: "Inspect route results"
  After: "Open War Board"

- Before: "Drop Deadline Board"
  After: "Drop Deadline Decisions"

- Before: "Which trade options save value before Roster Declaration Day?"
  After: "Which trade ideas may preserve value before Roster Declaration Day?"

- Before: "Which players are likely to enter the draft pool?"
  After: "Which players project as draft-pool candidates?"

- Before: "Display deterministic scores and recommendations."
  After: "Display deterministic scores, labels, and source assumptions."

- Before: "No Blocking Visual Bugs"
  After: "No visual bugs detected by automation; route evidence still requires review."

- Before: "Official Rank controls league rules. It is separate from private value, market value, and War Score."
  After: "Official Rank controls league rules. Keep it separate from Market Rank, War Room Rank, My Rank, and private value."

## Voice Rules
- Lead with the owner's decision: keep, drop, shop, trade, draft, or audit.
- Use concrete table labels before explanatory sentences.
- Keep analytical humility visible: "model output," "confidence," "source," "assumption," and "why."
- Do not imply predictions are certain; say "projects," "estimates," "flags," or "recalculates."
- Keep internal QA language out of first-screen product copy.
- Separate product copy from implementation copy: app labels should serve the Niners owner, docs can serve builders.
- Avoid fantasy-blog language, guru language, and hype.
- Preserve distinct labels for Official Rank, Market Rank, War Room Rank, and My Rank.

## Next 5 Copy Tasks
- [ ] Replace the root CTA with an owner-facing action such as "Open War Board"; keep route inspection language behind a QA disclosure.
- [ ] Review every visible page title for a concrete table job; avoid broad labels that do not say what the owner can decide.
- [ ] Add or confirm assumption/source labels near scenario and score tables; do not use certainty language for projections.
- [ ] Standardize rank column labels as Official Rank, Market Rank, War Room Rank, and My Rank wherever ranks appear.
- [ ] Rewrite visual QA status copy so automation cannot say "No Blocking Visual Bugs" when captured routes show "Not found."

## Stop Or Continue
continue but fix copy first