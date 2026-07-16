# Spreadsheet-Safe Encoding Contract

The final CSV boundary applies these rules to cell values:

1. Non-string values are returned unchanged.
2. A string beginning with an apostrophe is already protected and is returned
   unchanged.
3. Spaces and tabs are ignored only to find the first relevant character.
4. If that character is `=`, `+`, `-`, or `@`, an apostrophe is inserted before
   the complete original string.
5. Every other string is returned byte-for-byte unchanged by the encoder.

Examples:

| Input | Encoded value |
|---|---|
| `=1+1` | `'=1+1` |
| two spaces then `=1+1` | apostrophe, then the two spaces and `=1+1` |
| tab then `@SUM(1,1)` | apostrophe, then the tab and `@SUM(1,1)` |
| `'=1+1` | unchanged |
| `value = 1` | unchanged |
| numeric `-3` | unchanged numeric value |

The encoder does not parse formulas, modify CSV dialect behavior, normalize
Unicode, strip whitespace, or alter embedded newlines. Python's CSV writer or
pandas remains responsible for quoting and structure.
