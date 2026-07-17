# Type and CSV Preservation Review

## Direct typed controls

The encoder returned each value as the identical object with the exact type:

- negative integer and float;
- positive integer and float;
- `True` and `False`;
- `None`;
- `date`;
- timezone-aware `datetime`.

Numeric `-123` remains an integer. Textual `"-123"` remains a string and is
protected according to the formula-marker contract. No string is coerced to a
number.

## Text and CSV controls

Tests cover empty text, ordinary safe text, internal email `@`, URL `=`,
internal plus/minus, Unicode, numeric-looking safe text, already-protected
text, formula text with commas and double quotes, leading newlines, multiline
content, quoted-looking content, and Unicode formula content.

Both serializers were parsed independently. Protected cells equal the
apostrophe marker plus the complete input. Three-column sentinel rows prove
header and alignment preservation. The input dictionaries remain unchanged.

CSV quoting and formula protection are separately tested: ordinary quoting
without the cell marker is detected as unsafe.
