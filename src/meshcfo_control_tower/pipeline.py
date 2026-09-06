"""Control-tower orchestrator: playbooks + optional Nemotron refinement + CHP."""

from __future__ import annotations

from meshcfo_control_tower.catalog import load_fixture
from meshcfo_control_tower.config import Settings, get_settings
from meshcfo_control_tower.ledger import AuditLedger
from meshcfo_control_tower.llm import TokenFactoryClient, TokenFactoryError
from meshcfo_control_tower.market import fetch_market_context
from meshcfo_control_tower.playbooks import (
    buyer_seats,
    default_attacks,
    foundation_facts,
    icfr_gaps,
    intake_claims,
    next_actions,
    signal_summary,
    why_now_pack,
    build_sources,
)
from meshcfo_control_tower.provenance import apply_r0
from meshcfo_control_tower.schemas import (
    CHPReport,
    Claim,
    ModelInfo,
    PipelineEvent,
    RemediationBrief,
    SignalFixture,
)


def _collect_claims(brief: RemediationBrief) -> list[Claim]:
    claims: list[Claim] = []
    seen: set[str] = set()
    for claim in (
        *brief.why_now.triggers,
        *(gap.claim for gap in brief.icfr_gaps),
        *(action.claim for action in brief.next_actions),
        *brief.claims,
    ):
        if claim.claim_id in seen:
            continue
        seen.add(claim.claim_id)
        claims.append(claim)
    return claims


def _offline_brief(fixture: SignalFixture, settings: Settings) -> RemediationBrief:
    brief = RemediationBrief(
        company=fixture.company,
        signal=signal_summary(fixture),
        why_now=why_now_pack(fixture),
        buyer_seats=buyer_seats(fixture),
        icfr_gaps=icfr_gaps(fixture),
        next_actions=next_actions(fixture),
        claims=intake_claims(fixture),
        sources=build_sources(fixture),
        chp=CHPReport(foundation=foundation_facts(fixture), attacks=default_attacks(fixture)),
        model=ModelInfo(
            model=settings.nebius_model,
            fallback_model=settings.nebius_fallback_model,
            mode="offline",
        ),
        demo=True,
        pipeline=[
            PipelineEvent(agent="intake", phase="expand", summary="Loaded DEMO fixture and identity facts"),
            PipelineEvent(agent="why_now", phase="compress", summary="Mapped filing items to a regulatory clock"),
            PipelineEvent(agent="icfr", phase="expand", summary="Mapped excerpts to COSO / process gaps"),
            PipelineEvent(agent="ownership", phase="compress", summary="Assigned MeshCFO buyer seats and RACI"),
        ],
    )
    brief.claims = _collect_claims(brief)
    return brief


def _refine_with_nemotron(
    brief: RemediationBrief, fixture: SignalFixture, client: TokenFactoryClient
) -> None:
    excerpt_block = "\n\n".join(
        f"[{ex.source_id}] {ex.locator}: {ex.excerpt}" for ex in fixture.excerpts
    )
    user = (
        f"DEMO fixture_id={fixture.fixture_id} ticker={fixture.company.ticker}\n"
        f"Disclaimer: {fixture.demo_disclaimer}\n\n"
        f"Excerpts:\n{excerpt_block}\n\n"
        "Return JSON with keys:\n"
        "why_now_narrative (string),\n"
        "attacks (array of 3 short assumption attacks),\n"
        "board_line (one sentence the Audit Committee can read).\n"
        "Do not name real public companies. Do not add facts that are not in the excerpts."
    )
    payload = client.complete_json(
        system=(
            "You are the Cubiczan MeshCFO Control Tower composer. "
            "You produce governed ICFR remediation language with provenance. "
            "You never give free-form investment advice."
        ),
        user=user,
    )
    narrative = str(payload.get("why_now_narrative") or "").strip()
    board_line = str(payload.get("board_line") or "").strip()
    attacks = payload.get("attacks") or []
    if isinstance(attacks, list):
        extra = [str(a) for a in attacks if str(a).strip()]
        brief.chp.attacks = list(dict.fromkeys([*brief.chp.attacks, *extra]))[:8]
    if narrative:
        brief.why_now.triggers.append(
            Claim(
                text=f"Nemotron why-now synthesis: {narrative}",
                epistemic="inferred",
                agent="composer",
                expansion_step="compress:nemotron-why-now",
                grounding_source_ids=[fixture.excerpts[0].source_id, f"meta-{fixture.fixture_id}"],
                confidence="medium",
            )
        )
    if board_line:
        brief.why_now.triggers.append(
            Claim(
                text=f"AC one-liner: {board_line}",
                epistemic="inferred",
                agent="composer",
                expansion_step="compress:nemotron-board-line",
                grounding_source_ids=[fixture.excerpts[0].source_id],
                confidence="medium",
            )
        )
    brief.pipeline.append(
        PipelineEvent(
            agent="composer",
            phase="compose",
            summary=f"Nemotron synthesis on Token Factory ({client.model_used})",
        )
    )


def _adversary_pass(
    brief: RemediationBrief, fixture: SignalFixture, client: TokenFactoryClient | None
) -> None:
    brief.pipeline.append(
        PipelineEvent(
            agent="adversary",
            phase="attack",
            summary="CHP assumption attack on restatement/MW claims",
        )
    )
    if client is None:
        return
    try:
        payload = client.complete_json(
            system=(
                "You are the CHP adversary for Cubiczan MeshCFO. "
                "Attack unsupported leaps. Return JSON {\"attacks\": [string, ...]}."
            ),
            user=(
                f"DEMO only. Signal={fixture.signal_kind}. "
                f"Facts={fixture.structured_facts}. "
                "List 3 ways this brief could over-claim."
            ),
            max_tokens=800,
        )
        attacks = payload.get("attacks") or []
        if isinstance(attacks, list):
            brief.chp.attacks = list(
                dict.fromkeys([*brief.chp.attacks, *[str(a) for a in attacks]])
            )[:10]
    except TokenFactoryError:
        return


def run_brief(
    fixture_id: str,
    *,
    offline: bool = False,
    use_market: bool = True,
    settings: Settings | None = None,
    lock_validator: str | None = None,
) -> RemediationBrief:
    settings = settings or get_settings()
    fixture = load_fixture(fixture_id)
    brief = _offline_brief(fixture, settings)

    if use_market and settings.tavily_api_key:
        market_sources, note = fetch_market_context(fixture, settings.tavily_api_key)
        brief.sources.extend(market_sources)
        brief.market_context_note = note
        if market_sources:
            brief.pipeline.append(
                PipelineEvent(
                    agent="why_now",
                    phase="expand",
                    summary="Optional Tavily market context attached (not issuer evidence)",
                )
            )

    client: TokenFactoryClient | None = None
    if not offline and settings.live_llm_ready:
        try:
            client = TokenFactoryClient(settings)
            _refine_with_nemotron(brief, fixture, client)
            brief.model = ModelInfo(
                model=client.model_used,
                fallback_model=settings.nebius_fallback_model,
                mode="live",
                used_fallback=client.used_fallback,
                base_url=settings.nebius_base_url,
            )
        except TokenFactoryError as exc:
            brief.pipeline.append(
                PipelineEvent(
                    agent="composer",
                    phase="compose",
                    summary=f"Nemotron unavailable, staying on playbook: {exc}",
                )
            )

    brief.claims = _collect_claims(brief)
    _adversary_pass(brief, fixture, client)
    apply_r0(brief)
    brief.pipeline.append(
        PipelineEvent(
            agent="r0_gate",
            phase="gate",
            summary=f"lock_state={brief.lock_state} score={brief.chp.provenance_score}",
        )
    )

    if lock_validator and brief.lock_state == "PROVISIONAL_LOCK":
        brief.lock_state = "LOCKED"
        brief.chp.lock_rationale = (
            f"LOCKED after third-party validation by {lock_validator}. "
            + brief.chp.lock_rationale
        )
        brief.pipeline.append(
            PipelineEvent(
                agent="chp",
                phase="gate",
                summary=f"Validator {lock_validator} advanced lock to LOCKED",
            )
        )

    ledger = AuditLedger(settings.ledger_path, settings.audit_ledger_key or None)
    ledger.append(
        event=f"remediation_brief:{fixture.fixture_id}",
        actor="meshcfo_control_tower",
        inputs={
            "brief_id": brief.brief_id,
            "ticker": fixture.company.ticker,
            "lock_state": brief.lock_state,
            "model_mode": brief.model.mode,
            "model": brief.model.model,
        },
        sources=[s.source_id for s in brief.sources if s.kind == "edgar_excerpt"],
        confidence="high" if brief.chp.r0_passed else "medium",
        rationale=brief.chp.lock_rationale,
    )
    return brief
