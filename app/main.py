from __future__ import annotations

import streamlit as st

from src.config.constants import APP_NAME, V1_NAME
from src.config.settings import get_settings


def main() -> None:
    settings = get_settings()

    st.set_page_config(page_title=APP_NAME, layout="wide")
    st.title(APP_NAME)
    st.caption(V1_NAME)

    st.sidebar.header("War Room")
    st.sidebar.write(f"Active data pack: `{settings.active_data_pack}`")
    st.sidebar.write(f"Database: `{settings.database_path}`")

    st.subheader("Drop Deadline Command Center")
    st.write(
        "Official Rank controls league rules. War Score controls Niners strategy. "
        "Pick Value uses a 1,000-point local scale."
    )

    st.info("Task 0/1 shell is ready. Import, model, and board pages come next.")


if __name__ == "__main__":
    main()
