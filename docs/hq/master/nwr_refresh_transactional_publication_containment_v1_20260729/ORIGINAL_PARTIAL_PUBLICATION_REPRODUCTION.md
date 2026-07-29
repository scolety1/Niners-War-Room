# Original Partial-Publication Reproduction

The legacy algorithm staged five synthetic files and called `os.replace` once
per output. The fault injector raised `OSError` on replacement call two.

Observed result:

- replacement calls: 2;
- first output, `dp_freshness_report.csv`: new bytes visible;
- remaining four outputs: old bytes visible;
- mixed current set: `TRUE`;
- process exception: injected second-replacement failure.

This is an exact synthetic reproduction in a temporary directory. No live
opaque file was opened, parsed, or changed.

The reproduction proves that five independent replacements cannot be the
publication transaction. A failure on operation two leaves operation one
committed with no set-level rollback.
