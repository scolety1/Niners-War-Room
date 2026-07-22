# Original blocker reproduction

## A — manual workflow relabeled as automated

- Route: `/`, selected by `DEFAULT_ROOT_PAGE` in `app/navigation.py`.
- Render entry point: module execution of
  `app/pages/46_draft_cockpit_default_root.py`.
- Rendering functions: `page_header`, `render_workflow_tiles`, and Streamlit
  `link_button` calls.
- Workflow authority: the existing
  `ROUTE_AND_PRODUCT_SURFACE_INVENTORY.csv`, cross-checked against live
  `app.navigation` titles and targets.
- Current Trading Lab render: badge `Manual decision aid`, link
  `Open Trading Lab`, target `/trading-lab`.
- Old assertion: `tests/test_default_home_page.py` read source text and checked
  unrelated required/forbidden literals.
- Reproduction: replacing `Manual decision aid` with `Automated decision aid`
  still passed both old tests. The mutation survived because no rendered badge was
  captured or compared with workflow authority.

## B — unauthorized page-open write

- Render entry point: the same production root module.
- Reachable durable boundaries instrumented: `Path`/built-in/OS write-open,
  mkdir, touch, replace, rename, unlink/remove, copy/move/delete, receipt writers,
  draft/runtime writers, Development Lab writers, launcher backup/restore writers,
  refresh dispatch/status writers, pandas exports, and file-backed SQLite.
- Permitted: fake Streamlit session-state mutation that remains in memory.
- Prohibited: any durable mutation attempt or before/after tree/hash change.
- Reproduction: appending an actual `Path.write_text` call still passed both old
  tests; Streamlit `AppTest.from_string` executed it, wrote 16 bytes, and rendered
  with zero exceptions. The mutation survived because the old test inspected
  source literals and never executed the page or observed durable state.

## C — aggregate serialization

Metadata-only inventory recovered exactly: persistent 14 files / 542,801 bytes;
recovery 7 files / 172,878 bytes. Per-file paths, sizes, SHA-256 values, and
timestamps are in `PERSISTENT_STATE_DIGEST_REPRODUCTION.csv`. Repository-wide
targeted searches found no script, serializer, or command for the historical
aggregates. The original algorithm therefore cannot be recovered exactly from
available evidence and is not represented as verified.
