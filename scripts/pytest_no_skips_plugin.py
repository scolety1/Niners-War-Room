from __future__ import annotations

from pytest import ExitCode


def pytest_sessionfinish(session, exitstatus: int) -> None:
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        return
    prohibited = {
        name: len(reporter.stats.get(name, ()))
        for name in ("skipped", "xfailed", "xpassed")
        if reporter.stats.get(name)
    }
    if prohibited:
        reporter.write_line(f"PROHIBITED_NON_EXECUTION_RESULTS {prohibited}", red=True)
        session.exitstatus = ExitCode.TESTS_FAILED
