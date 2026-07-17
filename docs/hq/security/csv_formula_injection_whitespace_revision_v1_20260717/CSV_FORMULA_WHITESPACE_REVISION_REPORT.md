# CSV Formula Whitespace Revision Report

## Outcome

Outcome: `fixed`.

Verdict: `GREEN_CSV_FORMULA_INJECTION_WHITESPACE_REVISION_READY_FOR_HQ_REVIEW`.

The targeted successor corrects the rejected candidate's leading-whitespace
boundary without restarting or rewriting that candidate. The source-to-sink
boundary remains the shared `spreadsheet_safe_cell` encoder immediately before
Development Lab's pandas serializer and Draft Freeze's `csv.DictWriter`.

## Provenance

- Canonical remote HQ: `46d0f40eb5f1b00a7a993ed90958d37461aaa1b5`.
- Canonical tree: `487797f692ec132ad32c95044fdb810cfc3e33a1`.
- Rejected candidate: `work/csv-formula-injection-fix-v1-20260716` at
  `27ed532b01ddb7fc307a489b0c5bd6332ee70f4f`.
- Rejected candidate parent: canonical remote HQ above; exact distance one.
- Successor branch: `work/csv-formula-whitespace-revision-v1-20260717`.
- Successor worktree:
  `C:\NWR\Niners-War-Room-csv-formula-whitespace-revision-v1-20260717`.
- Push and HQ merge: not run.

The local branch named `work/hq-parallel-control` was not used as authority
because it had independently advanced. The fetched
`origin/work/hq-parallel-control` matched the controlling commit and tree.

## Vulnerable path and invariant

Separately authored or manual text can reach Development Lab's final pandas
CSV download. Draft Freeze board dictionaries reach its common final
`DictWriter`. The rejected helper located a formula marker only after ASCII
space or tab, so CR, LF, NBSP, and mixed prefixes reached both writers without
the spreadsheet-safe apostrophe.

The restored invariant is: for strings only, scan over the closed set SPACE,
TAB, CR, LF, and NBSP without modifying the input. If the next character is
`=`, `+`, `-`, or `@`, prefix the entire original string with an apostrophe at
index zero. Empty strings, safe strings, and all non-string values remain
unchanged. A string whose index-zero character is already the apostrophe
marker is unchanged, making repeated encoding behaviorally idempotent.

## Patch strategy

The narrowest complete repository-native change was to replace the helper's
two-character `lstrip` decision with an explicit index scan over the five
enumerated code points. No call site, model calculation, board builder,
ranking, source, trust-status behavior, or security automation changed.

## Security closure

- Pre-fix replay: `50 passed / 8 failed` across the two real boundaries.
- Corrected legacy boundary matrix: `58/58`.
- Expanded marker/whitespace boundary matrix: `112/112`.
- Combined adversarial boundary executions: `170/170`.
- Development Lab real-boundary executions: `85/85`.
- Draft Freeze real-boundary executions: `85/85`, plus `9/9` named board
  family contracts.
- Semantic mutation controls: `10/10 detected`.
- Direct helper and related focused file: `272 passed`.
- Owning and adjacent focused suite: `334 passed`.
- Official Hermetic Python collection: `2513 passed`, exit `0`.
- LocalData: `BLOCKED_MISSING_LOCAL_TEST_PACK`, zero collected, captured exit
  `4`.

The original issue no longer reproduces: CR-, LF-, NBSP-, mixed-, reverse-
mixed-, repeated-, and bounded-long prefixes recover as apostrophe-prefixed
cells after independent CSV parsing, and the suffix after the marker equals the
complete original input.

## Preserved behavior

Exact tests prove that numeric values remain the same Python objects and exact
types before serialization; typed negative values are not converted to
protected strings. Safe strings, booleans, nulls, empty strings, timestamps,
Unicode, commas, double quotes, line breaks, headers, and row/column alignment
remain governed by their existing writers. Source row dictionaries remain
unchanged.

## Remaining risk

No spreadsheet application was launched. The established repository contract
uses the conventional leading apostrophe marker, and client-specific behavior
outside that contract was not retested. No repository verification gap remains
for the requested correction.
