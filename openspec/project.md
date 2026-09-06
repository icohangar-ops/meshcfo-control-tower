# MeshCFO Control Tower

Cubiczan agentic office-of-the-CFO control tower. It turns labeled SEC EDGAR
material-weakness and restatement signals into governed remediation briefs
(why-now, buyer seat, ICFR gaps, next actions) with per-claim provenance.

## Stack

- Python 3.10+
- NVIDIA Nemotron via Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1/`)
- Streamlit control-tower UI + FastAPI + `meshcfo-brief` CLI
- Consensus Hardening Protocol (CHP) lock states: EXPLORING → PROVISIONAL_LOCK → LOCKED

## Constraints

- Env: `NEBIUS_API_KEY`. Never commit secrets.
- Public MIT.
- Sample fixtures are DEMO issuers, not fake real-company filings.
- Ownership is MeshCFO-style seats (RACI), not free-form advice.
