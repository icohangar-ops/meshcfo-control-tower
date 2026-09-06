from meshcfo_control_tower.catalog import list_fixtures, load_fixture


def test_fixtures_are_labeled_demo():
    rows = list_fixtures()
    assert {row["fixture_id"] for row in rows} == {"northstar", "lumenbridge", "cedarline"}
    for row in rows:
        assert "(DEMO)" in row["company"]
        fx = load_fixture(row["fixture_id"])
        assert fx.demo is True
        assert "DEMO" in fx.demo_disclaimer
        assert fx.company.demo is True
        assert all("DEMO" in excerpt.excerpt for excerpt in fx.excerpts)


def test_unknown_fixture():
    try:
        load_fixture("enron")
        assert False, "should have raised"
    except KeyError as exc:
        assert "northstar" in str(exc)
