from __future__ import annotations

LVE_SCORING = {
    "passing_yard": 1.0 / 30.0,
    "passing_td": 3.0,
    "interception": -1.0,
    "rushing_yard": 0.10,
    "rushing_td": 4.0,
    "receiving_yard": 0.10,
    "receiving_td": 4.0,
    "return_yard": 1.0 / 30.0,
    "return_td": 4.0,
    "reception": 0.0,
    "rushing_receiving_first_down": 0.40,
    "fumble_lost": -1.0,
}
