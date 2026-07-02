# Blocked Input Fields Report

Blocked from baseline shadow input:

- Candidate formula output or candidate rank.
- Production approval flags.
- App wiring, live preview, hidden sort, recommendation, or model-use flags.
- Market, ADP, vendor, projection, or external value fields as source truth.
- DynastyProcess market value/rank fields as candidate inputs.
- Routes, TPRR, YPRR, route proxies, red-zone sidecars, and ambiguous `rz_att`.
- Current-only roster/status/injury/depth/schedule context as model features.
- Raw/local export paths or secrets.

The generated export keeps only static review identity, rank, position-rank, tier/bucket, and sanitized review-status fields.
