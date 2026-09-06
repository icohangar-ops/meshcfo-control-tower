from meshcfo_control_tower.provenance import apply_r0
from meshcfo_control_tower.schemas import (
    CHPReport,
    Claim,
    CompanyRef,
    GroundingSource,
    ICFRGap,
    ModelInfo,
    NextAction,
    RemediationBrief,
    SignalSummary,
    WhyNow,
)


def _brief(claims: list[Claim]) -> RemediationBrief:
    source = GroundingSource(
        source_id="s1",
        kind="edgar_excerpt",
        locator="DEMO",
        excerpt="excerpt",
        demo_label=True,
    )
    gap_claim = claims[0] if claims else Claim(
        text="gap",
        epistemic="verified",
        agent="icfr",
        expansion_step="x",
        grounding_source_ids=["s1"],
    )
    action_claim = claims[0] if claims else gap_claim
    return RemediationBrief(
        company=CompanyRef(display_name="X (DEMO)", ticker="X-DEMO", cik="DEMO", demo=True),
        signal=SignalSummary(
            fixture_id="t",
            signal_kind="material_weakness",
            forms=["10-K"],
            filed_on="2026-01-01",
            period_end="2025-12-31",
            headline="demo",
        ),
        why_now=WhyNow(urgency="immediate", regulatory_clock="now", triggers=claims[:1]),
        icfr_gaps=[
            ICFRGap(
                coso_component="Control Activities",
                process="demo",
                deficiency_type="design",
                severity="material_weakness",
                summary="demo",
                claim=gap_claim,
            )
        ],
        next_actions=[
            NextAction(
                owner_seat="CFO",
                action="act",
                due="now",
                evidence_required="ev",
                claim=action_claim,
            )
        ],
        claims=claims,
        sources=[source],
        chp=CHPReport(foundation=["f"]),
        model=ModelInfo(model="test", mode="offline"),
    )


def test_r0_drops_ungrounded_claim():
    good = Claim(
        text="grounded",
        epistemic="verified",
        agent="intake",
        expansion_step="e",
        grounding_source_ids=["s1"],
    )
    bad = Claim(
        text="hallucination",
        epistemic="inferred",
        agent="composer",
        expansion_step="e",
        grounding_source_ids=["does-not-exist"],
    )
    brief = apply_r0(_brief([good, bad]))
    ids = {c.claim_id for c in brief.claims}
    assert good.claim_id in ids
    assert bad.claim_id not in ids
    assert bad.claim_id in brief.chp.r0_dropped_claim_ids
    assert brief.lock_state == "EXPLORING"


def test_r0_passes_when_all_grounded():
    good = Claim(
        text="grounded",
        epistemic="verified",
        agent="intake",
        expansion_step="e",
        grounding_source_ids=["s1"],
    )
    brief = apply_r0(_brief([good]))
    assert brief.chp.r0_passed is True
    assert brief.lock_state == "PROVISIONAL_LOCK"
