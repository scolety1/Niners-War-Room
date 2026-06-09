# Model v4 Football Sanity Beliefs

These are user-supplied dynasty sanity beliefs for a 10-team, 1QB, non-PPR LVE
format with 0.4 rushing/receiving first-down scoring. They are not manual
overrides and they are not final rankings.

Model v4 must either align with these beliefs or produce receipt-backed,
source-backed reasons for disagreeing. The user confirmed these are review-only
guardrails, not must-pass manual overrides. If the model strongly disagrees
without a clear explanation, the ranking is a bug, data gap, or formula review
item.

## Source Handling

- Treat these as sanity-test priors, not imported data.
- External claims inside the beliefs should be verified before being used as
  cited evidence.
- Do not tune formulas directly to these statements.
- Convert them into regression fixtures and audit prompts.

## Beliefs

1. Bijan Robinson is the premier dynasty running back.
   - Sanity expectation: Bijan should be RB1 or require an extremely clear
     receipt-backed exception.
   - A model that places non-elite, fragile, old, or low-confidence RBs above
     Bijan needs review.

2. Jahmyr Gibbs is a cornerstone dynasty RB just behind Bijan.
   - Sanity expectation: Gibbs should sit in the elite RB tier and generally be
     near Bijan.
   - A model that treats Gibbs as merely a replaceable RB is wrong.

3. Christian McCaffrey remains an elite RB but sits behind the younger
   workhorses.
   - Sanity expectation: McCaffrey can remain valuable, but age and injury
     window should keep him behind younger cornerstone RBs in dynasty value.

4. De'Von Achane is an elite or core dynasty RB.
   - Sanity expectation: Achane should not be treated as a generic bubble
     player without a clear injury/role/confidence explanation.
   - If the model shops or releases Achane, that must trigger a blocking audit.

5. Jaxon Smith-Njigba is an elite/top-tier dynasty WR.
   - Sanity expectation: JSN should be in the elite WR tier unless sources show
     a major injury, role, identity, or data problem.
   - JSN below much weaker or older WR profiles should trigger review.

6. Puka Nacua is an elite dynasty WR asset.
   - Sanity expectation: Puka belongs in the elite WR tier and should not be
     penalized without clear source-backed injury/role reasons.

7. Ja'Marr Chase remains a top-tier dynasty WR.
   - Sanity expectation: Chase should remain in the elite WR tier.
   - A down-year adjustment cannot push him below ordinary WR starters without
     strong evidence.

8. Justin Jefferson is still a core dynasty WR despite a down season.
   - Sanity expectation: Jefferson remains a core/elite WR unless receipts show
     a verified, durable role or health collapse.

9. Amon-Ra St. Brown is a cornerstone dynasty receiver.
   - Sanity expectation: Amon-Ra should remain a core WR because target earning
     and production stability matter heavily in this format.

10. Malik Nabers and CeeDee Lamb are core dynasty wide receivers in the same
    general tier.
    - Sanity expectation: both should be treated as core WR assets.
    - Large separation between them should require receipt-backed explanation.

11. In a 1QB league, replaceable quarterbacks should not be prioritized over
    elite RBs and WRs.
    - Sanity expectation: only true difference-maker QBs can compete near the
      top dynasty assets.
    - Replaceable or merely solid starting QBs should be suppressed.

12. Aging veterans like Keenan Allen should not outrank young cornerstone
    running backs.
    - Sanity expectation: older declining WRs should not rank above Bijan,
      Gibbs, Achane, or comparable cornerstone young RBs.
    - If an aging veteran outranks a cornerstone RB, trigger an age/dropoff and
      formula-balance audit.

## Fixture Families To Build

### Elite RB Tier

- Bijan Robinson should anchor RB1.
- Jahmyr Gibbs should be near Bijan.
- De'Von Achane should be treated as core unless injury/role evidence clearly
  lowers confidence.
- Christian McCaffrey should remain high but age/dropoff should matter.

### Elite WR Tier

- JSN, Puka Nacua, Ja'Marr Chase, Justin Jefferson, Amon-Ra St. Brown, Malik
  Nabers, and CeeDee Lamb should all land in core/elite WR territory unless
  source evidence explains otherwise.

### 1QB Suppression

- Replaceable QBs must not crowd out elite RBs/WRs.
- Elite QB exceptions require start security and true difference-making scoring.

### Age Dropoff

- Aging veterans must receive visible age/dropoff treatment.
- Aging veteran production can matter, but it cannot override dynasty window
  without receipts.

### Failure Triggers

- Achane labeled as `bubble` without a strong explanation.
- Bijan not RB1.
- Gibbs far below Bijan without a strong explanation.
- JSN below clearly weaker/older WRs without a strong explanation.
- Keenan Allen or similar aging WR above young cornerstone RBs.
- Replaceable QBs above elite RB/WR assets.

## Required Model Behavior

For each fixture, Model v4 must output:

- compared players
- expected relationship or tier
- actual relationship or tier
- pass/fail/review status
- top receipt drivers
- source gaps
- formula component explanation
- whether the issue is data, identity, normalization, formula, or acceptable
  model disagreement
