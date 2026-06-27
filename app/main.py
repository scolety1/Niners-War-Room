from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.components.ui_framework import apply_app_shell
from app.navigation import (
    HIDDEN_ADVANCED_PAGES,
    VISIBLE_NAVIGATION_PAGE_GROUPS,
    app_page_path,
)
from src.config.constants import APP_NAME


def main() -> None:
    app_dir = Path(__file__).resolve().parent
    st.set_page_config(page_title=APP_NAME, layout="wide")
    apply_app_shell()
    visible_page_groups = {
        section: [
            st.Page(
                app_page_path(app_dir, spec),
                title=spec.title,
                url_path=spec.url_path,
                default=spec.default,
                visibility=spec.visibility,
            )
            for spec in specs
        ]
        for section, specs in VISIBLE_NAVIGATION_PAGE_GROUPS
    }
    hidden_pages = [
        st.Page(
            app_page_path(app_dir, spec),
            title=spec.title,
            url_path=spec.url_path,
            default=spec.default,
            visibility=spec.visibility,
        )
        for spec in HIDDEN_ADVANCED_PAGES
    ]
    navigation = st.navigation(
        {
            **visible_page_groups,
            "Hidden compatibility routes": hidden_pages,
        },
        position="top",
    )
    navigation.run()


if __name__ == "__main__":
    main()
