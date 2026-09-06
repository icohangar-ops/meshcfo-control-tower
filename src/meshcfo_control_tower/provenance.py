"""R0 provenance gate — ungrounded claims never enter the locked artifact."""

from __future__ import annotations

from meshcfo_control_tower.schemas import (
    CHPReport,
    Claim,
    GroundingSource,
    RemediationBrief,
    WhyNow,
)


def source_registry(sources: list[GroundingSource]) -> dict[str, GroundingSource]:
    return {s.source_id: s for s in sources}


def claim_is_grounded(claim: Claim, registry: dict[str, GroundingSource]) -> bool:
    if not claim.grounding_source_ids:
        return False
    return all(sid in registry for sid in claim.grounding_source_ids)


def apply_r0(brief: RemediationBrief) -> RemediationBrief:
    registry = source_registry(brief.sources)
    kept: list[Claim] = []
    dropped: list[str] = []

    for claim in brief.claims:
        if claim_is_grounded(claim, registry):
            kept.append(claim)
        else:
            dropped.append(claim.claim_id)
            claim.chp_finding = "R0: dropped — missing or unknown grounding source"

    kept_ids = {c.claim_id for c in kept}

    def _keep_claim(claim: Claim) -> bool:
        return claim.claim_id in kept_ids and claim_is_grounded(claim, registry)

    why_triggers = [c for c in brief.why_now.triggers if _keep_claim(c)]
    gaps = [g for g in brief.icfr_gaps if _keep_claim(g.claim)]
    actions = [a for a in brief.next_actions if _keep_claim(a.claim)]

    total = max(len(brief.claims), 1)
    score = round(len(kept) / total, 3)
    passed = bool(kept) and not dropped and score >= 1.0 and bool(gaps) and bool(actions)

    lock_state: str
    if passed:
        lock_state = "PROVISIONAL_LOCK"
        rationale = (
            "R0 passed: every retained claim has a known source. "
            "LOCKED requires a named third-party validator."
        )
    else:
        lock_state = "EXPLORING"
        rationale = (
            f"R0 incomplete: dropped {len(dropped)} ungrounded claim(s); "
            f"provenance_score={score}."
        )

    brief.claims = kept
    brief.why_now = WhyNow(
        urgency=brief.why_now.urgency,
        regulatory_clock=brief.why_now.regulatory_clock,
        triggers=why_triggers,
    )
    brief.icfr_gaps = gaps
    brief.next_actions = actions
    brief.chp = CHPReport(
        foundation=brief.chp.foundation,
        attacks=brief.chp.attacks,
        r0_passed=passed,
        r0_dropped_claim_ids=dropped,
        provenance_score=score,
        lock_rationale=rationale,
    )
    brief.lock_state = lock_state  # type: ignore[assignment]
    return brief
