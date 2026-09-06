"""FastAPI surface for the same pipeline the CLI and Streamlit UI use."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from meshcfo_control_tower import __version__
from meshcfo_control_tower.catalog import list_fixtures
from meshcfo_control_tower.config import get_settings
from meshcfo_control_tower.pipeline import run_brief
from meshcfo_control_tower.schemas import RemediationBrief

app = FastAPI(
    title="Cubiczan MeshCFO Control Tower",
    description=(
        "Governed ICFR remediation briefs from labeled DEMO EDGAR material-weakness "
        "and restatement signals. NVIDIA Nemotron on Nebius Token Factory."
    ),
    version=__version__,
)


class BriefRequest(BaseModel):
    fixture_id: str = Field(default="northstar")
    offline: bool = False
    use_market: bool = True
    lock_validator: str | None = None


@app.get("/health")
def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "ok": True,
        "brand": "Cubiczan",
        "product": "MeshCFO Control Tower",
        "token_factory": settings.nebius_base_url,
        "model": settings.nebius_model,
        "live_llm_ready": settings.live_llm_ready,
    }


@app.get("/fixtures")
def fixtures() -> list[dict[str, str]]:
    return list_fixtures()


@app.post("/brief", response_model=RemediationBrief)
def create_brief(req: BriefRequest) -> RemediationBrief:
    try:
        return run_brief(
            req.fixture_id,
            offline=req.offline,
            use_market=req.use_market,
            lock_validator=req.lock_validator,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
