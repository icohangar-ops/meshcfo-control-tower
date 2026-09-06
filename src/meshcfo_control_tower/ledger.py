"""Tamper-evident HMAC-SHA256 chained JSONL audit ledger (MeshCFO-style)."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEMO_LEDGER_KEY = "meshcfo-control-tower-demo-ledger-key"


def _canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class AuditLedger:
    def __init__(self, path: Path, key: str | None = None) -> None:
        self.path = path
        self.key = (key or DEMO_LEDGER_KEY).encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def _last_sig(self) -> str:
        last = ""
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last = json.loads(line).get("sig", "")
        return last

    def append(
        self,
        *,
        event: str,
        actor: str,
        inputs: dict[str, Any],
        sources: list[str],
        confidence: str | None = None,
        rationale: str | None = None,
    ) -> str:
        body = {
            "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "event": event,
            "actor": actor,
            "inputs": inputs,
            "sources": sources,
            "confidence": confidence,
            "rationale": rationale,
            "prev_sig": self._last_sig(),
        }
        digest = hmac.new(
            self.key,
            (_canonical(body) + body["prev_sig"]).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        body["sig"] = digest
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(body, ensure_ascii=False) + "\n")
        return digest

    def verify(self) -> tuple[bool, int | None]:
        prev = ""
        with self.path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if not line.strip():
                    continue
                record = json.loads(line)
                sig = record.pop("sig", "")
                expected = hmac.new(
                    self.key,
                    (_canonical(record) + record.get("prev_sig", "")).encode("utf-8"),
                    hashlib.sha256,
                ).hexdigest()
                if sig != expected or record.get("prev_sig", "") != prev:
                    return False, index
                prev = sig
        return True, None
