# Design: MeshCFO Control Tower

## Pipeline

```
fixture (DEMO) → source registry
  → Intake Agent (signal facts)
  → Why-Now Agent (urgency + clock)
  → ICFR Gap Agent (COSO + process)
  → Ownership Agent (buyer seats / RACI)
  → Composer (governed brief)
  → Adversary (CHP attack)
  → R0 gate (drop ungrounded claims)
  → PROVISIONAL_LOCK | EXPLORING
  → signed JSONL ledger
```

Live mode: Nemotron (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`) via Token Factory
refines specialist JSON. Offline mode: deterministic playbooks from fixture
fields so tests and CI run without secrets.

## Provenance

Every claim carries: agent, expansion step, epistemic tag
(`verified` | `inferred` | `pattern-match`), grounding source IDs, CHP finding.
R0 rejects claims with missing or unknown sources.

## Ownership

Seats are roles, not invented named executives: CFO, Controller, Internal Audit,
SOX PMO, Process Owner, Audit Committee, CIO/CISO. RACI is assigned per gap.

## Market context

Optional Tavily search is labeled `market_context` and never used as issuer
evidence for a DEMO fixture.
