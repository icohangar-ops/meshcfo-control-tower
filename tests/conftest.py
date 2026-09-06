import os

import pytest


@pytest.fixture(autouse=True)
def isolate_ledger(tmp_path, monkeypatch):
    monkeypatch.setenv("MESHCFO_LEDGER_PATH", str(tmp_path / "audit.jsonl"))
    os.environ["MESHCFO_LEDGER_PATH"] = str(tmp_path / "audit.jsonl")
