from __future__ import annotations

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("28_settings_data_health_v1.py")), run_name="__main__")
