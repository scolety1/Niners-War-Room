# Trust Banner Structural Call Review

## Recognition rule

The helper parses routed Python with `ast.parse`. A component call counts only
when an exact symbol is imported from its exact repository module and an
`ast.Call` invokes the local name established by that import. An explicit
`as` alias is accepted only for that exact import; arbitrary similarly named
functions, attribute lookalikes, and symbols from other modules are rejected.

The governed symbols are:

- `app.components.decision_trust_strip.render_decision_trust_strips`;
- `app.components.trust_status.render_page_trust_banner`; and
- imported `REVIEW_ONLY_SURFACE_BANNER` passed to `st.warning` for the legacy
  Decision Board contract.

Comments contribute no AST nodes. String literals are `ast.Constant`, not
`ast.Call`. Imported-but-unused and differently named calls both count as zero.
Duplicate primary calls count as two and fail the exact-one assertion.

## Results

The current routed Decision Trust Strip pages, legacy component-banner pages,
legacy constant-banner page, and Draft Prep gate pass. Removed, comment-only,
string-only, duplicate, unused-import, differently named, and unrelated-module
variants are all detected. Raw source substring counting is absent from the
revised component-call assertions.
