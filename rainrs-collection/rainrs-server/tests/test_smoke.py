"""Smoke tests for the rainrs_server package scaffold."""

import rainrs_server


def test_package_imports() -> None:
    assert rainrs_server.__version__
