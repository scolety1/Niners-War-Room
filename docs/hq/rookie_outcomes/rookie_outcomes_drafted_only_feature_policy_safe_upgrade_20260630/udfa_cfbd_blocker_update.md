# UDFA and CFBD Blocker Update

UDFA modeling remains blocked. The historical entry-status artifact contains `0` confirmed UDFA rows and `2514` likely UDFA / needs-review rows. Current-rookie review-only UDFA decisions do not become historical source truth, model input, or training truth.

Draft absence cannot confirm UDFA. Player stats, rosters, weekly rosters, depth charts, snap counts, injuries, games, starts, awards, career length, and fantasy outcomes cannot confirm UDFA.

CFBD remains review-only unless human-approved identity links exist. CFBD identity candidates, production context, transfer/timeline context, and school/position fields may support review packets only. They are not model input, training truth, source truth, or a way to bypass identity review.

Required future gates:

- UDFA source-policy gate with direct approved evidence.
- CFBD human identity approval and production/source approval.
- Separate model gate before any model/training use.
