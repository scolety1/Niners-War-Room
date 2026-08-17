# Waiver Wire Findings

NWR has the raw league pieces but not a complete Waiver Wire decision workflow. Sleeper rosters and player identity can derive the active unrostered pool; transactions can supply historical claims. The K/DST lane is narrower external consensus, not a general waiver engine.

## Clean architecture

`Sleeper roster state → active unrostered pool → weekly/ROS evidence → legal-lineup optimizer → add/drop pair marginal gain → priority/confidence/freshness`

Required outputs: recommended add, paired drop, weeks helped, starting-lineup marginal points, ROS/bench value, bye/injury replacement, roster constraint, confidence, source freshness and waiver status. Keep projection, Market and NWR value separate.

The unlicensed `playjukeff/wire-room` supplied the best conceptual pattern: evaluate legal-lineup improvement for each add/drop pair and model claim sequencing. Reimplement; copy no code. FAAB should be deferred until NWR has trustworthy transaction history, budget state and calibration. Early releases may provide ranges/rationale explicitly labeled heuristic.

No Sleeper writes. The owner executes claims on-platform.
