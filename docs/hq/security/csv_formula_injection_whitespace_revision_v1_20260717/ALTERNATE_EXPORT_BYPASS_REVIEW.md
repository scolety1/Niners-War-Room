# Alternate Export Bypass Review

## Development Lab

All ten static `csv_download` calls, representing the current CSV download
actions, converge on the single pandas wrapper at lines 638-642. The other
download controls in the component emit JSON. There is no second `to_csv`,
`csv.writer`, `DictWriter`, cached raw CSV byte path, compressed CSV path,
index-bearing export, or post-encoding formatter in the affected component.

## Draft Freeze

All nine board families converge on `_write_csv`. The seven readiness,
health, coverage, trust, calibration, admission, and certificate CSV siblings
also use that writer. The only nearby copy operation preserves an existing
source-pack `model_outputs.csv` as backup; it is not a generated board export.
There is no alternate affected board writer, compressed variant, index column,
cached raw byte path, or formatting/coercion step after encoding.

## Disposition

Both affected surfaces reach the shared encoder immediately before their real
serializer. No alternate bypass remains. Unrelated sibling exporters were not
adopted into this correction.
