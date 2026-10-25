"""Offline tests for the CLI entry point."""

import sys

from statcard.__main__ import main


def test_cli_rejects_bad_riot_id(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["statcard", "valorant", "NoTagHere"])
    assert main() == 1
    assert "Name#TAG" in capsys.readouterr().err


def test_cli_rejects_empty_tag(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["statcard", "valorant", "Name#"])
    assert main() == 1
    assert "Name#TAG" in capsys.readouterr().err


def test_cli_rejects_unknown_region(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["statcard", "valorant", "Name#TAG", "--region", "mars"])
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover - argparse always exits
        raise AssertionError("argparse should reject an unknown region")
