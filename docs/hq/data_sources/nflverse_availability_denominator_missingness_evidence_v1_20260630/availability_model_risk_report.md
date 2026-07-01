# Availability Model Risk Report

## Result

Health inference, model, training, and source-truth use remain blocked for every audited denominator field.

## Risks If Promoted Prematurely

- Missing snap/stat rows could be misread as zero snaps or zero production.
- Missing injury reports could be misread as healthy or clean.
- Missing roster rows could be misread as off-roster or inactive.
- Current-season rows could leak future availability if no point-in-time as-of replay is enforced.
- Per-game denominator choices could create label leakage if aligned after outcomes are known.
- `games_missed_while_rostered` could become a fabricated target if inferred from incomplete evidence.

## Required Before Any Non-Display Use

A future lane must provide historical replay, point-in-time source availability, label parity, leakage audit, identity gate, censoring policy, missingness tests, and explicit user approval. Until then, all audited fields remain display/review-only or blocked.
