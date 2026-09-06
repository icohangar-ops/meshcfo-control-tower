# Change: Add MeshCFO Control Tower

## Why

Audit committees and CFOs get EDGAR material-weakness and restatement signals as
unstructured filings. MeshCFO already owns auditable CFO artifacts; this change
adds a control-tower surface that converts those signals into a governed
remediation brief with named buyer seats and per-claim provenance.

## What Changes

- Ingest labeled DEMO EDGAR-style fixtures (8-K Item 4.02, 10-K/10-Q Item 9A)
- Run a specialist agent mesh (intake, why-now, ICFR, ownership, adversary, composer)
- Call NVIDIA Nemotron on Nebius Token Factory for live synthesis
- Emit a JSON remediation brief from CLI; render it in Streamlit and FastAPI
- Gate claims through CHP (foundation → attack → R0 provenance → lock)

## Impact

- New capability: `remediation-briefs`
- No existing production specs (greenfield repo)
