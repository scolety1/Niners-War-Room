from __future__ import annotations

import runpy
from pathlib import Path

PAGE_PATH = Path(__file__).with_name("21_live_draft_room_v1.py")

runpy.run_path(str(PAGE_PATH), run_name="__main__")
