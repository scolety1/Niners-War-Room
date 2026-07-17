# Development Lab Export Revalidation

## Boundary

`app/components/development_lab.py::csv_download` transforms rows with
`spreadsheet_safe_rows`, constructs a pandas `DataFrame`, serializes with
`to_csv(index=False)`, and passes the result to the download control. The
correction does not modify this call site.

## Result

- Legacy 29-case matrix: `29/29`.
- Expanded four-marker by fourteen-prefix matrix: `56/56`.
- Total Development Lab real-boundary executions: `85/85`.

Every result was parsed with Python's independent `csv.DictReader` using a
three-column row with left/right sentinels. Protected cells began with the
apostrophe marker, the remaining string exactly equaled the input, and headers,
one-row alignment, Unicode, commas, quotes, and line breaks remained valid.

Disabling `spreadsheet_safe_rows` at this exact module boundary is detected by
the semantic mutation suite.
