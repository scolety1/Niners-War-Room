# Final Encoder Contract

`src/utils/spreadsheet_safe.py` is the single shared encoder for the affected
CSV boundaries.

For each input cell:

1. A non-string value is returned unchanged, including its exact type.
2. An empty string is returned unchanged.
3. A string already beginning with the safety apostrophe is returned unchanged,
   which makes repeated encoding behaviorally idempotent.
4. Inspection advances across any sequence drawn only from this closed set:
   U+0020 SPACE, U+0009 TAB, U+000D CR, U+000A LF, and U+00A0 NBSP.
5. If the first relevant character is `=`, `+`, `-`, or `@`, an apostrophe is
   inserted at index zero.
6. Every original character, including leading whitespace, Unicode, quoting,
   commas, and line breaks, follows the marker unchanged.
7. Otherwise the original string is returned unchanged.

This is inspection without trimming or normalization. Actual numeric negative
values such as integer `-123` and float `-123.5` remain numeric until their
chosen CSV writer serializes them. Only final serialized untrusted textual CSV
cells can change.

The contract is enforced at both actual boundaries:

- Development Lab: `pd.DataFrame(spreadsheet_safe_rows(rows)).to_csv(...)`.
- Draft Freeze: the sole `csv.DictWriter` calls
  `writer.writerows(spreadsheet_safe_rows(rows))`.

No model, ranking, scoring, source-admission, trust-status, or draft calculation
uses the encoded values.
