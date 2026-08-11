from __future__ import annotations

# Streamlit executes this file with app/ first on sys.path; package imports follow bootstrap.
# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from app.components.ui_framework import apply_app_shell


def main() -> None:
    app_dir = Path(__file__).resolve().parent
    st.set_page_config(page_title="Niners War Room — Redraft", layout="wide")
    apply_app_shell()
    navigation = st.navigation(
        [
            st.Page(
                app_dir / "pages" / "52_redraft_v1.py",
                title="Redraft War Room",
                default=True,
            )
        ],
        position="top",
    )
    navigation.run()


if __name__ == "__main__":
    main()
