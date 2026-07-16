# CSV Formula-Injection Fix Report

## Outcome

The two verified low-severity findings are fixed by one centralized string-cell
encoder applied at the final CSV boundary:

- `csf_202db9b3638e9bdd15b848e9` / `CAND-review-019-02` / `DG002`
- `csf_d31d2c747a31aba0207d8683` / `CAND-review-019-04` / `DG019`

`spreadsheet_safe_cell` prefixes an apostrophe before the original string when
its first character after spaces or tabs is `=`, `+`, `-`, or `@`. The original
whitespace, Unicode, quoting, and line breaks remain intact. Non-string values
remain non-strings until the selected CSV writer serializes them.

The encoder is used only by Development Lab downloads and Draft Freeze board
files. No ranking, formula-model, source admission, freshness, ordering, or
recommendation behavior changed.

## Evidence and disposition

Current-HQ PoCs reproduced both sinks before modification. Development Lab
emitted `  =1+1`; Draft Freeze emitted a tab followed by `@SUM(1,1)`. After the
fix, the same cells serialize as `'  =1+1` and a leading apostrophe followed by
the original tab and `@SUM(1,1)`. Numeric controls serialize normally.

Both findings are `FIXED`. The implementation is a local-only optional lane and
must not be pushed without a separate human review and authorization.

## Assumptions and residual risk

The documented interoperability contract uses the conventional leading
apostrophe text marker. Spreadsheet consumers that intentionally remove that
marker before formula evaluation are outside this exporter boundary. Values
already beginning with an apostrophe are treated as protected and remain
unchanged; this makes repeated encoding idempotent.

## Artifacts

- `src/utils/spreadsheet_safe.py`
- `app/components/development_lab.py`
- `src/services/draft_freeze_service.py`
- `tests/test_spreadsheet_safe_csv.py`
- this security packet
