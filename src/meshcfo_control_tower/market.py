"""Optional Tavily market-context enrichment. Never treated as issuer evidence."""

from __future__ import annotations

import httpx

from meshcfo_control_tower.schemas import GroundingSource, SignalFixture


def fetch_market_context(
    fixture: SignalFixture, api_key: str, timeout: float = 12.0
) -> tuple[list[GroundingSource], str | None]:
    if not api_key.strip():
        return [], None

    topic = {
        "revenue_recognition": "SEC material weakness revenue recognition restatement Item 4.02 ICFR",
        "itgc_access": "SOX ITGC privileged access material weakness Item 9A",
        "inventory_reserves": "inventory obsolescence reserve material weakness restatement ICFR",
    }
    area = fixture.process_areas[0] if fixture.process_areas else "period_end_close"
    query = topic.get(
        area,
        "SEC EDGAR material weakness restatement ICFR remediation SOX 404",
    )
    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 3,
                "include_answer": True,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return [], None

    sources: list[GroundingSource] = []
    for index, hit in enumerate(data.get("results") or [], start=1):
        excerpt = (hit.get("content") or "")[:400]
        url = hit.get("url") or "tavily"
        if not excerpt:
            continue
        sources.append(
            GroundingSource(
                source_id=f"mkt-{fixture.fixture_id}-{index}",
                kind="market_context",
                locator=f"Tavily market context (not issuer evidence): {url}",
                excerpt=excerpt,
                demo_label=True,
            )
        )
    answer = data.get("answer")
    note = None
    if sources or answer:
        note = (
            "Market context from Tavily is thematic SOX/ICFR background only. "
            "It is not evidence about this DEMO issuer and is not used as an "
            "EDGAR grounding source for R0-verified claims."
        )
        if answer:
            note = f"{note} Tavily summary: {answer[:280]}"
    return sources, note
