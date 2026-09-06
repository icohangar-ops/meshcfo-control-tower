from meshcfo_control_tower.ledger import AuditLedger


def test_ledger_chain_verifies(tmp_path):
    path = tmp_path / "audit.jsonl"
    ledger = AuditLedger(path, key="test-key")
    ledger.append(event="a", actor="t", inputs={"n": 1}, sources=["s1"], rationale="one")
    ledger.append(event="b", actor="t", inputs={"n": 2}, sources=["s1"], rationale="two")
    ok, idx = ledger.verify()
    assert ok is True
    assert idx is None


def test_ledger_detects_tamper(tmp_path):
    path = tmp_path / "audit.jsonl"
    ledger = AuditLedger(path, key="test-key")
    ledger.append(event="a", actor="t", inputs={}, sources=[], rationale="x")
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("\"event\": \"a\"", "\"event\": \"TAMPER\""), encoding="utf-8")
    ok, idx = ledger.verify()
    assert ok is False
    assert idx == 0
