# Draft Freeze Export Revalidation

## Boundary

`src/services/draft_freeze_service.py::_write_csv` builds the field-name union,
writes the header, and passes `spreadsheet_safe_rows(rows)` directly to
`csv.DictWriter.writerows`. The correction does not modify this call site.

## Result

- Legacy 29-case matrix: `29/29`.
- Expanded four-marker by fourteen-prefix matrix: `56/56`.
- Total Draft Freeze real-boundary executions: `85/85`.
- Named board-family contracts: `9/9`.

Files were opened for independent parsing with `newline=""`, preserving the
original CR/LF content exactly. Protected cells began with the marker and the
suffix exactly equaled the original input. Field order, headers, one-row
alignment, typed numeric serialization, commas, quotes, Unicode, and multiline
content remained valid.

Disabling `spreadsheet_safe_rows` at this exact writer boundary is detected by
the semantic mutation suite.
