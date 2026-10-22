"""Tests for the development printing helper and the CLI parser."""

from __future__ import annotations

import pytest

from rainrs_server.cli import _build_parser, main
from rainrs_server.process.dev import ENV_DEV_PRINT, dev_print, dev_print_enabled


def test_dev_print_is_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv(ENV_DEV_PRINT, raising=False)
    assert dev_print_enabled() is False

    dev_print("hello %s", "world")

    assert capsys.readouterr().out == ""


def test_dev_print_writes_to_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(ENV_DEV_PRINT, "1")
    assert dev_print_enabled() is True

    dev_print("hello %s", "world")

    assert capsys.readouterr().out == "[dev] hello world\n"


def test_dev_print_ignores_false_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_DEV_PRINT, "off")
    assert dev_print_enabled() is False


def test_cli_parser_exposes_the_stages() -> None:
    parser = _build_parser()

    process = parser.parse_args(["process", "--conf", "0.4"])
    assert process.command == "process"
    assert process.conf == 0.4

    derive = parser.parse_args(["derive", "--bits", "32", "--binding", "xor"])
    assert derive.bits == 32
    assert derive.binding == "xor"


def test_cli_requires_a_command() -> None:
    with pytest.raises(SystemExit):
        _build_parser().parse_args([])


def test_cli_main_rejects_unknown_commands() -> None:
    with pytest.raises(SystemExit):
        main(["unknown"])
