# Route and AST Inspection Decision

## Authoritative route contract

`app/navigation.py` is the authoritative route registry. Its
`ALL_NAVIGATION_PAGES` tuple combines the visible and hidden `NavigationPageSpec`
declarations. `app/main.py` consumes those same declarations to construct every
Streamlit `st.Page`, using the repository-native `app_page_path` resolver. There
is no second runtime route table.

The registry declares visible `/rankings` and hidden compatibility
`/player-board` routes. Both currently target `pages/20_final_board_v1.py`, which
resolves to `app/pages/20_final_board_v1.py`. That routed module invokes
`page_header("Dynasty Rankings", ...)` and owns the current Player Board labels.
The four-line `app/pages/05_rankings.py` app-shell wrapper is not the target of
either route.

## Routed trust presentations

The trust-banner tests will identify governed pages by route name, resolve each
name through `ALL_NAVIGATION_PAGES`, and inspect only the resolved source. The
governed contracts are explicit by presentation type:

- Decision Trust Strip routes require exactly one structurally proven
  `render_decision_trust_strips(...)` call and no legacy primary-banner call.
- Legacy decision/model routes require exactly one structurally proven
  `render_page_trust_banner(...)` call and no competing primary-banner call.
- The legacy Decision Board requires the imported
  `REVIEW_ONLY_SURFACE_BANNER` value to be passed to one `st.warning(...)` call.
- legacy Draft Prep requires its scouting/legal-pool gate in the routed
  `st.markdown(...)` call and its planning-only disclosure in a routed
  `st.info(...)` call.

The governed route-name lists are test expectations; their file targets are
not duplicated. Every target is obtained from the production registry supplied
to the resolver.

## Structural Python inspection

Python source will be parsed with `ast.parse`. A component invocation counts
only when all of these conditions hold:

1. the component is imported from its exact repository module;
2. an `ast.Call` calls the local name established by that exact import; and
3. the call occurs in the routed module being inspected.

Repository source currently uses direct `from ... import ...` names. The helper
will recognize an explicit `as` alias only when it aliases the exact supported
symbol imported from the exact supported repository module. It will not accept
attribute calls, locally defined lookalikes, arbitrary similarly named calls,
or imports from other modules.

Comments are absent from the AST. String literals containing a function name
remain `ast.Constant` nodes and cannot become `ast.Call` nodes. An imported but
unused component therefore contributes zero calls. Missing imports, missing
files, duplicate routes, missing routes, syntax errors, wrong targets, missing
calls, and duplicate calls all fail closed with an assertion identifying the
route or source.

The Player Board title will be proven as the first literal argument of the
structurally resolved `page_header(...)` call, not as an arbitrary text
occurrence. Other current UI labels will be read as exact AST string values from
that same routed owner, excluding comments and unrelated files.

## Duplicate, missing, and wrong-wrapper detection

The route resolver will build a route map only after proving every registered
URL is unique. A requested route must have exactly one declaration, its target
must remain inside `app/`, and its resolved file must exist. Player Board checks
will additionally require both aliases to resolve to the canonical target.

Trust contracts will count the expected primary call structurally and require
the count to equal one. A missing call yields zero; a duplicate yields two. If a
route is injected to a wrapper, the wrapper source is what gets inspected, so a
bannerless wrapper or a wrapper with only an unrelated banner fails even when a
valid call remains in another module.

## Reuse and narrowness decision

The implementation will reuse the production `NavigationPageSpec`,
`ALL_NAVIGATION_PAGES`, and `app_page_path` objects. Existing route tests use
these objects but do not provide duplicate detection, injected disposable route
copies, or exact-import AST call recognition. A single helper under `tests/`
will add only those missing test concerns.

This is the narrowest reliable harness because it changes no application code,
does not duplicate the production route table, does not import routed Streamlit
pages for execution, and supports every required mutation with immutable route
copies or injected source text. Parser and resolution errors remain visible and
cannot be swallowed, skipped, or converted to alternate accepted states.
