"""Offline tests for the CLI entry point."""

import sys

from statcard.__main__ import main


def test_cli_rejects_bad_riot_id(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["statcard", "valorant", "NoTagHere"])
    assert main() == 1
    assert "Name#TAG" in capsys.readouterr().out
