# AST Call Inspection Review

`tests/ui_contract_harness.py` parses routed Python with `ast.parse`. A governed
component call counts only when the exact symbol is imported from its exact
repository module and an `ast.Call` invokes the resulting local name. Explicit
aliases of the exact import are accepted; attribute lookalikes, differently
named calls, local lookalikes, and imports from other modules are excluded.

The independent review confirmed:

- comments contribute zero calls;
- string literals contribute zero calls;
- imported-but-unused symbols contribute zero calls;
- a differently named function contributes zero calls;
- an unrelated module cannot satisfy a routed owner;
- a missing call fails with count zero;
- a duplicate primary call fails with count two; and
- routed wrappers are inspected instead of a fixed implementation file.

The Player Board title is the first literal argument to the structurally
resolved `page_header(...)` call. The review-only component contract parses the
owning function and requires one `with st.expander(details_label)` context.

Result: `PASS_FAIL_CLOSED_PYTHON_AST_INSPECTION`.
