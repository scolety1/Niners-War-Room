# Pro Audit 1: Formula And Football Logic

You are auditing Model v4, a local-first dynasty fantasy football model for a 10-team, 1QB, non-PPR league with first-down scoring.

Goal:
Verify that the formula system is analyzing player value correctly, football-wise and league-format-wise. Do not tune to personal rankings. Audit whether the formulas, components, replacement/VORP discipline, lifecycle adjustments, and confidence caps are coherent and safe.

League format:
- 10 teams
- 1QB
- non-PPR
- first-down scoring
- no TE premium
- return yards 1 per 30
- return TD 4

Audit focus:
1. Verify the Phase 11A formula contract is strict enough:
   - no generic JSON slurping
   - no market/rank/projection leakage into private football value
   - current prospects only from admitted sources
   - missing data cannot become zero/average/positive evidence
2. Verify replacement/VORP logic:
   - replacement levels make sense for 10-team 1QB
   - QB and TE values are disciplined
   - mid QB/TE production cannot outrank elite RB/WR value without real VORP gap
3. Verify RB/WR/QB/TE current value modules:
   - RB role/first-down/age logic makes football sense
   - WR target/route/yardage/first-down logic is appropriately weighted
   - QB rushing and 1QB scarcity are handled carefully
   - TE no-premium values require real replacement gap
4. Verify lifecycle/archetype layer:
   - does not invent traits
   - aging and role-fragility warnings are visible
   - rushing-age QB caution is handled without overreacting
5. Verify confidence/missingness:
   - caps are visible and enforceable
   - missing route/target/snap evidence does not become false certainty
6. Review named-player sanity:
   - Lamar Jackson
   - Josh Allen
   - Brock Purdy
   - Christian McCaffrey
   - Bijan Robinson
   - Jahmyr Gibbs
   - Ja'Marr Chase
   - Puka Nacua
   - Jaxon Smith-Njigba
   - Brock Bowers
   - George Kittle
   - Travis Kelce
7. Identify suspicious formulas or outputs that need repair before final decision use.

Please answer with:
1. Overall verdict: ready / needs formula repair / needs source repair / needs architecture repair
2. Critical blockers
3. High/medium/low issues
4. Player examples supporting each issue
5. Whether the model is league-adjusted for this exact format
6. Whether formula outputs are ready for human decision review
7. Recommended next repairs, if any

Constraints:
- Do not ask for new data unless a specific missing source materially blocks decisions.
- Do not suggest using ADP, rankings, or projections as private football value.
- Do not tune formulas to match consensus rankings.
