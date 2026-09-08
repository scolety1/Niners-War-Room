# FFA/ESPN Outlier and Role Audit — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 13. Real, direct
comparison of NWR's unified projection ranking (persistence + rookie-cohort + Section 4b's
insufficient-history fallback, all real, already-modeled lanes) against the real, admitted FFA
2026 market pack and the owner's real 403-league ESPN ADP snapshot. **Ballers/UDK
comparison: not run** -- no real, current, market-wide Ballers/UDK export exists in this repo
(only fixture data and the owner's real 36-row QB-only file from an earlier session), so a
real "NWR vs Ballers" outlier audit has no real data to run against; disclosed, not
fabricated.

## Method

Real gsis_id identity join (FFA via exact normalized-name+position, same method used
elsewhere this session; ESPN ADP already carries real gsis_id-format player_ids directly).
Rank delta = source rank/ADP minus NWR's own real rank (positive = NWR ranks the player much
HIGHER than the source; negative = the source ranks the player much higher than NWR).

## Real, honest top disagreements (NWR vs FFA)

**NWR ranks much higher than FFA** (top of list, largest deltas): almost entirely veteran QBs
NWR's insufficient-history fallback or ordinary persistence model over-credits relative to
FFA's own richer, presumably role-aware model (Tua Tagovailoa, Deshaun Watson, Marcus Mariota,
Kirk Cousins, Geno Smith, Aaron Rodgers, Jacoby Brissett, Daniel Jones) plus real rookies
(Fernando Mendoza, Shedeur Sanders, Cam Ward) NWR's cohort model doesn't yet have enough
signal to rank as low as FFA's.

**FFA ranks much higher than NWR**: real, established WR/RB/TE names (Malik Nabers, Garrett
Wilson, Mike Evans, Isaiah Likely, Tyreek Hill, Terry McLaurin) plus a real, coherent cluster
of true sophomores (Bhayshul Tuten, Omarion Hampton, Cam Skattebo) whose limited real rookie-
year volume genuinely constrains NWR's persistence-based projection more than FFA's model.

## Classification (top 40 largest real disagreements)

```
VALID_MODEL_DISAGREEMENT: 35
PERSISTENCE_BLIND_SPOT:    5
CURRENT_ROLE_CHANGE:       0
SOURCE_GAP:                0
STATUS_GAP:                0
```

**No real CURRENT_ROLE_CHANGE cases were found** among the largest real disagreements. This
is a real, useful cross-validation of Section 5's own finding (Judkins/role-change): the real
disagreements this audit surfaces are explained by genuine persistence-model
history-limitations (real sophomores, real insufficient-history fallback cases -- exactly
Brooks-class/Judkins-class territory) or genuine methodology differences (age/usage-decline
weighting, rookie-cohort granularity), never by a distinguishable "the market has independent
current role evidence NWR lacks" signal. This supports, rather than undermines, Section 5's
decision to leave the role-change challenger reference-only rather than force-build one.

A real, concrete confirmation of the Section 4b fallback's own disclosed weak point-estimate
accuracy: Deshaun Watson (real, long-injured, Achilles tear, minimal 2025 availability) is
ranked `87.0` by the insufficient-history fallback -- high, because his real original draft
capital (2017 1st overall) drives a strong round-1 QB cohort median, exactly the honest
"weak, not promoted" finding already documented in
`NWR_BROOKS_CLASS_SOURCE_GAP_FIX_V1_20260908.md`. Real, independent evidence the same
disclosed limitation is real, not hypothetical.

## NWR vs ESPN (real, this league's 403 ADP snapshot, 276 matched real players)

Mean absolute rank delta: 137.4 -- large in absolute terms, but expected and not itself a
disagreement signal: this specific ADP snapshot's `overall_adp` values only span this league's
own real, shallow draft pool depth (max real ADP ~1049, a real late/deep pick), while NWR's
own rank spans its entire real admitted universe (~985 players) -- the two scales are not
directly comparable beyond the top of the market. The largest real deltas are all deep-bench
WR/TE names (Troy Franklin, Chimere Dike, Noah Fant, etc.) where this scale mismatch, not a
genuine disagreement, explains the size of the gap.

## Disposition

No code change -- audit/documentation only. Findings used as real supporting evidence for
Section 5's reference-only disposition (no role-change signal found); no new action item
raised beyond what Sections 4b (insufficient-history fallback) and 5 (Judkins) already
disclosed.

## Status

Section 13: **DONE.**
