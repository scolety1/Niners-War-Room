# Rendered workflow disposition contract

The harness resolves `/` through `DEFAULT_ROOT_PAGE`, reads the resolved production
module, and executes that module in an isolated Streamlit recorder. The recorder
passes the real `ui_framework` renderer its calls and parses emitted HTML with
`html.parser`; it does not search the page for broad substrings.

Captured structures are H1/H2/H3/H4 headings, body text, badges, link labels,
link destinations, tile title/status/detail, and tile-to-link containment.

For every tile:

1. Exactly one primary link must render.
2. The destination must resolve through `app.navigation`.
3. The production route title must equal the rendered tile title.
4. The existing 60-route audit classification must agree with the rendered
   controlled disposition label.
5. Unknown or contradictory disposition labels fail closed.

The contract also requires one `Niners War Room` H1, four primary tiles, six
unique links, and no duplicate target. Authority classifications are loaded from
the source audit packet and are validated against production navigation on each
run; no new per-route disposition table exists in the test.

Negative controls cover manual -> automated, gated -> live, review-only ->
production, parked -> available, wrong route target, missing primary link, and a
contradictory manual/automated badge. Every control is detected.
