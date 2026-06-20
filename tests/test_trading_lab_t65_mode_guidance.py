from src.trading_lab.trade_lab_ui import TRADE_LAB_MODES, mode_context_for, mode_guidance_lines


def test_every_mode_has_help_text() -> None:
    for mode in TRADE_LAB_MODES:
        context = mode_context_for(mode)
        assert context.explanation
        assert context.input_focus
        assert context.output_meaning
        assert context.fixture_caveat


def test_every_mode_has_user_question_label() -> None:
    for mode in TRADE_LAB_MODES:
        assert "?" in mode_context_for(mode).user_question


def test_mode_guidance_lines_include_expected_labels() -> None:
    for mode in TRADE_LAB_MODES:
        lines = mode_guidance_lines(mode)
        assert any(line.startswith("Question:") for line in lines)
        assert any(line.startswith("Input focus:") for line in lines)
        assert any(line.startswith("Output meaning:") for line in lines)
        assert any(line.startswith("Caveat:") for line in lines)


def test_no_mode_claims_real_integration() -> None:
    text = " ".join(line for mode in TRADE_LAB_MODES for line in mode_guidance_lines(mode)).lower()

    for blocked in ("real integration is wired", "public fantasy source wired", "real roster data"):
        assert blocked not in text


def test_no_automated_decisioning_language() -> None:
    text = " ".join(line for mode in TRADE_LAB_MODES for line in mode_guidance_lines(mode)).lower()

    for blocked in ("auto-submit", "submit trade", "automatic decision", "execute trade"):
        assert blocked not in text
