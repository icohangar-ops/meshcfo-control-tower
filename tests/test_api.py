from fastapi.testclient import TestClient

from meshcfo_control_tower.api import app

client = TestClient(app)


def test_health_and_fixtures():
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["brand"] == "Cubiczan"
    assert "tokenfactory.nebius.com" in body["token_factory"]
    assert "Nemotron" in body["model"] or "nvidia" in body["model"]

    fixtures = client.get("/fixtures")
    assert fixtures.status_code == 200
    ids = {row["fixture_id"] for row in fixtures.json()}
    assert ids == {"northstar", "lumenbridge", "cedarline"}


def test_post_offline_brief():
    response = client.post(
        "/brief",
        json={"fixture_id": "northstar", "offline": True, "use_market": False},
    )
    assert response.status_code == 200
    brief = response.json()
    assert brief["company"]["ticker"] == "NSMT-DEMO"
    assert brief["demo"] is True
    assert brief["lock_state"] in {"PROVISIONAL_LOCK", "LOCKED"}
