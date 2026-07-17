# Leading Whitespace Security Contract

## Closed set

The security-relevant leading-whitespace set is exactly:

| Name | Code point | Python representation |
|---|---:|---|
| SPACE | U+0020 | `" "` |
| HORIZONTAL TAB | U+0009 | `"\t"` |
| CARRIAGE RETURN | U+000D | `"\r"` |
| LINE FEED | U+000A | `"\n"` |
| NO-BREAK SPACE | U+00A0 | `"\u00a0"` |

Any leading sequence composed only of these characters is recognized,
including mixed, repeated, reverse-mixed, and bounded-long sequences.
`str.isspace()`, Unicode normalization, trimming, and unrestricted whitespace
classes are intentionally not used.

## Formula markers and safety marker

The formula marker set is exactly `=`, `+`, `-`, and `@`. The established
spreadsheet-safe marker is the apostrophe (`U+0027`). For a matching string,
the safety marker is inserted at index zero before every original character.

The encoder never strips, trims, normalizes, collapses, reorders, or coerces the
input. The exact original leading sequence remains at indexes one onward.

## Typed boundary

Only `str` values are inspected. Integers, floats, booleans, null values,
dates, datetimes, and other typed values return as the identical object with
the identical type. Empty strings and ordinary safe strings return unchanged.
