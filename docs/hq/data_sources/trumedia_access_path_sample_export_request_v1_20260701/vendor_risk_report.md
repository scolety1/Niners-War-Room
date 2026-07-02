# Vendor Risk Report

Vendor: TruMedia Networks

Verdict: `YELLOW_ACCESS_POSSIBLE_LICENSE_REQUIRED_SAMPLE_EXPORT_REQUEST_ONLY`

## Risk Matrix

| Risk | Impact | Current status | Mitigation |
|---|---|---|---|
| No public self-service NFL signup | NWR cannot evaluate without vendor response. | Open blocker. | Use public email/demo route and request evaluation sample. |
| Enterprise/team/media eligibility | NWR may not qualify for access. | Likely. | Ask directly whether private research/fantasy evaluation is eligible. |
| Third-party field rights | PFF, tracking, coverage, or partner fields may not be exportable or reusable. | High risk. | Request field-level rights matrix and license note. |
| Private fantasy/dynasty research rights | Intended NWR use may be outside standard terms. | Unknown. | Ask for written permission covering private formula research and derived artifacts. |
| Local storage and derived artifacts | Even sample exports may have retention or storage limits. | Unknown. | Ask before accepting data; store outside repo until confirmed. |
| Exact NFL fields not public | Routes, TPRR, YPRR, alignment, coverage, matchup, and separation may vary by product. | Open blocker. | Request schema dictionary and sample export. |
| Identity joins | GSIS/PFF IDs may be available, Sleeper IDs likely not native. | Partial evidence. | Ask for GSIS/PFF IDs and local Sleeper join permission. |
| Missing/zero ambiguity | Sparse or absent rows could be misread as zero. | High risk. | Require explicit zero/missing semantics. |
| API credential handling | Tokens could leak if handled casually. | Controlled by policy. | Prefer sample export first; use secure secrets handling if API is approved. |
| Source-truth overreach | Teams could treat vendor data as approved too early. | Controlled by guardrails. | Keep all outputs review-only and blocked from production lanes. |

## Biggest Blockers

1. Confirming NWR eligibility for any evaluation access.
2. Getting written rights for private fantasy/dynasty formula research.
3. Confirming exportability of tracking, route, coverage, matchup, and third-party fields.
4. Confirming local storage and derived artifact rights.
5. Getting stable IDs and explicit missing/zero semantics.

## Risk Verdict

TruMedia is worth contacting for a rights-cleared sample export. It is not safe to integrate, model, train, tune, rank, or source-promote without a separate rights and source-admission decision.

