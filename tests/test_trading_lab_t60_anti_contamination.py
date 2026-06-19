from pathlib import Path

from src.trading_lab.trade_lab_component import trade_lab_label_text

SOURCE_ROOT = Path("src/trading_lab")


def source_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_ROOT.glob("*.py"))


def import_lines() -> list[str]:
    return [
        line.strip()
        for line in source_text().splitlines()
        if line.strip().startswith(("import ", "from "))
    ]


def test_source_modules_do_not_import_blocked_lanes() -> None:
    text = "\n".join(import_lines()).lower()

    for blocked in ("outcome", "rookie", "mock_draft", "drop_decision", "deployment", "master"):
        assert blocked not in text


def test_source_modules_do_not_contain_prohibited_route_or_deploy_strings() -> None:
    text = source_text().lower()

    for blocked in ("streamlit navigation", "st.page", "deploy", "local_exports", "data/"):
        assert blocked not in text


def test_ui_labels_do_not_claim_real_integration() -> None:
    text = trade_lab_label_text().lower()

    for blocked in (
        "real nwr integration wired",
        "public fantasy market source wired",
        "review queue saved",
        "real roster integration wired",
    ):
        assert blocked not in text


def test_old_wall_street_active_purpose_terms_absent_from_ui_labels() -> None:
    text = trade_lab_label_text().lower()

    for blocked in ("stock", "broker", "crypto", "equity", "order execution"):
        assert blocked not in text
