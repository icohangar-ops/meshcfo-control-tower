"""Load labeled DEMO fixtures from package data."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from meshcfo_control_tower.schemas import SignalFixture

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

_FILES = {
    "northstar": "northstar_materials_demo.json",
    "lumenbridge": "lumenbridge_payments_demo.json",
    "cedarline": "cedarline_health_demo.json",
}


@lru_cache(maxsize=8)
def load_fixture(fixture_id: str) -> SignalFixture:
    key = fixture_id.strip().lower()
    if key not in _FILES:
        known = ", ".join(sorted(_FILES))
        raise KeyError(f"Unknown fixture '{fixture_id}'. Known DEMO fixtures: {known}")
    payload = json.loads((FIXTURE_DIR / _FILES[key]).read_text(encoding="utf-8"))
    fixture = SignalFixture.model_validate(payload)
    if not fixture.demo:
        raise ValueError("Refusing to load a fixture that is not labeled demo=true")
    return fixture


def list_fixtures() -> list[dict[str, str]]:
    rows = []
    for fixture_id in _FILES:
        fx = load_fixture(fixture_id)
        rows.append(
            {
                "fixture_id": fx.fixture_id,
                "company": fx.company.display_name,
                "ticker": fx.company.ticker,
                "signal_kind": fx.signal_kind,
                "forms": ", ".join(fx.forms),
                "disclaimer": fx.demo_disclaimer,
            }
        )
    return rows
