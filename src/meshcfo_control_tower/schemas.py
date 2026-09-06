"""Governed brief schemas — ownership and provenance, not free-form advice."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

Epistemic = Literal["verified", "inferred", "pattern-match"]
Confidence = Literal["high", "medium", "low"]
LockState = Literal["EXPLORING", "PROVISIONAL_LOCK", "LOCKED"]
Raci = Literal["A", "R", "C", "I"]
Urgency = Literal["immediate", "this_quarter", "this_cycle"]
DeficiencyType = Literal["design", "operating", "both"]
Severity = Literal["material_weakness", "significant_deficiency", "control_deficiency"]
SourceKind = Literal[
    "edgar_excerpt",
    "fixture_metadata",
    "market_context",
    "coso_framework",
    "ownership_playbook",
]
BuyerSeatName = Literal[
    "CFO",
    "Controller",
    "Internal Audit",
    "SOX PMO",
    "Process Owner",
    "Audit Committee",
    "CIO/CISO",
]
SignalKind = Literal["material_weakness", "restatement", "both"]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


class CompanyRef(BaseModel):
    display_name: str
    ticker: str
    cik: str
    demo: bool = True
    industry: str = ""


class EdgarExcerpt(BaseModel):
    source_id: str
    form: str
    item: str
    locator: str
    filed_on: str
    excerpt: str


class SignalFixture(BaseModel):
    """Labeled DEMO EDGAR-style signal. Not a real SEC registrant."""

    fixture_id: str
    demo: bool = True
    demo_disclaimer: str
    company: CompanyRef
    signal_kind: SignalKind
    forms: list[str]
    filed_on: str
    period_end: str
    auditor_demo: str = ""
    process_areas: list[str] = Field(default_factory=list)
    excerpts: list[EdgarExcerpt]
    structured_facts: dict[str, str] = Field(default_factory=dict)


class GroundingSource(BaseModel):
    source_id: str
    kind: SourceKind
    locator: str
    excerpt: str
    demo_label: bool = True


class Claim(BaseModel):
    claim_id: str = Field(default_factory=lambda: _id("clm"))
    text: str
    epistemic: Epistemic
    agent: str
    expansion_step: str
    grounding_source_ids: list[str] = Field(default_factory=list)
    chp_finding: str | None = None
    confidence: Confidence = "medium"


class WhyNow(BaseModel):
    urgency: Urgency
    regulatory_clock: str
    triggers: list[Claim] = Field(default_factory=list)


class BuyerSeat(BaseModel):
    seat: BuyerSeatName
    raci: Raci
    accountable_for: str
    named_role: str
    process_area: str = ""


class ICFRGap(BaseModel):
    gap_id: str = Field(default_factory=lambda: _id("gap"))
    coso_component: str
    process: str
    deficiency_type: DeficiencyType
    severity: Severity
    summary: str
    claim: Claim
    compensating_controls: list[str] = Field(default_factory=list)


class NextAction(BaseModel):
    action_id: str = Field(default_factory=lambda: _id("act"))
    owner_seat: BuyerSeatName
    action: str
    due: str
    evidence_required: str
    claim: Claim


class CHPReport(BaseModel):
    foundation: list[str] = Field(default_factory=list)
    attacks: list[str] = Field(default_factory=list)
    r0_passed: bool = False
    r0_dropped_claim_ids: list[str] = Field(default_factory=list)
    provenance_score: float = 0.0
    lock_rationale: str = ""


class ModelInfo(BaseModel):
    provider: str = "Nebius Token Factory"
    base_url: str = "https://api.tokenfactory.nebius.com/v1/"
    model: str
    fallback_model: str | None = None
    mode: Literal["live", "offline"] = "offline"
    used_fallback: bool = False


class SignalSummary(BaseModel):
    fixture_id: str
    signal_kind: SignalKind
    forms: list[str]
    filed_on: str
    period_end: str
    headline: str


class PipelineEvent(BaseModel):
    ts: str = Field(default_factory=_now)
    agent: str
    phase: Literal["expand", "compress", "attack", "gate", "compose"]
    summary: str


class RemediationBrief(BaseModel):
    brief_id: str = Field(default_factory=lambda: _id("brf"))
    generated_at: str = Field(default_factory=_now)
    demo: bool = True
    brand: str = "Cubiczan"
    product: str = "MeshCFO Control Tower"
    company: CompanyRef
    signal: SignalSummary
    why_now: WhyNow
    buyer_seats: list[BuyerSeat] = Field(default_factory=list)
    icfr_gaps: list[ICFRGap] = Field(default_factory=list)
    next_actions: list[NextAction] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    sources: list[GroundingSource] = Field(default_factory=list)
    chp: CHPReport = Field(default_factory=CHPReport)
    model: ModelInfo
    lock_state: LockState = "EXPLORING"
    pipeline: list[PipelineEvent] = Field(default_factory=list)
    market_context_note: str | None = None

    def provenance_index(self) -> dict[str, GroundingSource]:
        return {s.source_id: s for s in self.sources}
