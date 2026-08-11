# Redraft app separation

Two owner-facing entry points now exist:

- `app/main.py`: **Niners War Room — Dynasty**
- `app/main_redraft.py`: **Niners War Room — Redraft**

`scripts/start_redraft_app.ps1` starts the Redraft app on port 8512. It exposes league profiles, rankings, tiers, position rankings, current-season Player Compare, Draft Board, Cheat Sheet, and Data Health. Both shells share `redraft_engine_v1_service.py`; projection data and profile persistence are not duplicated. Redraft state remains under its separate root.
