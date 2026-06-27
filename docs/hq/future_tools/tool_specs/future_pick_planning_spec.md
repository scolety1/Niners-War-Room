# Future Pick Planning Spec - Framework Only

Purpose: manual inventory/review tool for future picks and draft assets.

Safe output now: manual inventory/checklist framework.

Blocked output: pick valuation, trade fairness, class-adjusted pick recommendation.

Required data: manual/runtime trade events, official traded-pick source if imported, pick year/round/original owner, and review notes.

Proposed mechanics: list picks and evidence source. No numeric pick value or market/NWR valuation.

Current NWR coverage: Live Draft V2 records future pick assets as manual/runtime evidence. This is not source truth.

Build decision: `SAFE_NOW_FRAMEWORK_ONLY`.

Safety notes: do not value picks or use DynastyProcess, ADP, or market as trade value.

Next step: create an inventory-only component after route needs are prioritized.

Sources: Sleeper API docs https://docs.sleeper.com/.
