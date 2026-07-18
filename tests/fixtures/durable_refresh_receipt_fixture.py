from __future__ import annotations

import os
from pathlib import Path

from app.components.durable_refresh_receipt_panel import (
    render_durable_refresh_receipt_panel,
)
from src.services.refresh_receipt_store_service import load_refresh_receipt

receipt_path = Path(os.environ["NWR_REFRESH_RECEIPT_TEST_PATH"])
render_durable_refresh_receipt_panel(
    load_refresh_receipt(status_path=receipt_path),
    title="Controlled durable receipt fixture",
)
