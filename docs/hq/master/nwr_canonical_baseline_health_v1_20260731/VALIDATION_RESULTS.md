# Validation Results

- Exact baseline registry: PASS, 14/14 files; paths, sizes, hashes, schemas,
  widths, rows, dataset-specific grains, rights, identities, and temporal rules.
- Raw snapshot immutability: PASS, 14/14 unchanged.
- Weekly schema repair: PASS, 76,804/76,804 duplicate column blocks equal;
  deterministic derived 146-column UTF-8/LF CSV is 34,914,253 bytes with SHA-256
  `103f267575843c84fe6d3be6d4cbe6352ee619cf4266321ccd01f85b2bd71581`.
- Seasonal mixed-schema defect: truthfully quarantined in full; no false Green.
- Dataset-specific grain: PASS or explicit fail-closed quarantine for every row;
  depth-chart exact duplicates = 207.
- Crosswalk behavior: PASS; all provider collision values and blank GSIS rows
  block resolution; name-only fallback is prohibited.
- Temporal policy: PASS; post-game, report-time, season-end, completed-season,
  pre-game-snapshot, current-only, and retrieval-only cutoffs are explicit.
- Negative mutations: PASS, 10/10 rejected.
- Outcome V3 fresh-checkout repair: PASS at authoritative SHA-256
  `e3b44047d36bd62d9573295db64d96f214922a20f0083cf49105f104970b3d20`.
- Model/source admission: NONE; six open source controls remain fail-closed.
- Focused validator tests: PASS, 5/5.
- Applicable Hermetic, passive Data Health, receipt-truth, negation-security,
  controller, and Phase 1B regression slice: PASS, 91/91 (required unsandboxed
  rerun because the sandbox token cannot authenticate governed Windows paths).
- Security controls: PASS, 20/20.
- Independent adoption, applicable regression, two-root deterministic output,
  remote reread, conditional push, and stable synchronization are required at closeout.
