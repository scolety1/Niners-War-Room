from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.components.ui_framework import apply_app_shell
from app.navigation import ALL_NAVIGATION_PAGES, app_page_path
from src.config.constants import APP_NAME


def main() -> None:
    app_dir = Path(__file__).resolve().parent
    st.set_page_config(page_title=APP_NAME, layout="wide")
    apply_app_shell()
    pages = [
        st.Page(
            app_page_path(app_dir, spec),
            title=spec.title,
            url_path=spec.url_path,
            default=spec.default,
            visibility=spec.visibility,
        )
        for spec in ALL_NAVIGATION_PAGES
    ]
    navigation = st.navigation(pages, expanded=False)
    navigation.run()


if __name__ == "__main__":
    main()
