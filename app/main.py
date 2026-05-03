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
        "Start with the table that answers the current decision, then drill into the "
        "model audit only when a score needs proof."
    )

    status_columns = st.columns(3)
    status_columns[0].metric("Active pack", settings.active_data_pack)
    status_columns[1].metric("Command boards", "7")
    status_columns[2].metric("Runtime", "Local only")

    st.markdown(
        """
        **Primary boards**

        - Import Review: source checks, warnings, and pack readiness
        - Team: Niners keeper pressure and forced-release view
        - War Board: sortable drop, shop, hold, and shield decisions
        - Trade Central, Draft Room, League Intel, and Model Audit for deeper proof
        """
    )


if __name__ == "__main__":
    main()
