from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.trading_lab.trade_lab_component import render_trade_lab_page

render_trade_lab_page()
