"""Deterministic MeshCFO playbooks — ownership mesh, not free-form advice."""

from __future__ import annotations

from meshcfo_control_tower.schemas import (
    BuyerSeat,
    Claim,
    GroundingSource,
    ICFRGap,
    NextAction,
    PipelineEvent,
    SignalFixture,
    SignalSummary,
    WhyNow,
)

COSO = {
    "control_environment": "Control Environment",
    "risk_assessment": "Risk Assessment",
    "control_activities": "Control Activities",
    "information": "Information & Communication",
    "monitoring": "Monitoring",
}

FRAMEWORK_SOURCES = [
    GroundingSource(
        source_id="coso-icfr",
        kind="coso_framework",
        locator="COSO Internal Control — Integrated Framework (ICFR mapping playbook)",
        excerpt="ICFR deficiencies are evaluated by COSO component and by whether the deficiency is design, operating, or both.",
        demo_label=True,
    ),
    GroundingSource(
        source_id="meshcfo-raci",
        kind="ownership_playbook",
        locator="MeshCFO Control Tower ownership playbook",
        excerpt="Buyer seats are CFO (A for certifications), Controller (R for close/policy), process owner (R for transaction evidence), Internal Audit (R for remediation testing), SOX PMO (R for matrix), Audit Committee (I/oversight), CIO/CISO (R for ITGC).",
        demo_label=True,
    ),
]


def build_sources(fixture: SignalFixture) -> list[GroundingSource]:
    sources = [
        GroundingSource(
            source_id=ex.source_id,
            kind="edgar_excerpt",
            locator=ex.locator,
            excerpt=ex.excerpt,
            demo_label=True,
        )
        for ex in fixture.excerpts
    ]
    sources.append(
        GroundingSource(
            source_id=f"meta-{fixture.fixture_id}",
            kind="fixture_metadata",
            locator=f"DEMO fixture metadata:{fixture.fixture_id}",
            excerpt=fixture.demo_disclaimer
            + " "
            + "; ".join(f"{k}={v}" for k, v in fixture.structured_facts.items()),
            demo_label=True,
        )
    )
    sources.extend(FRAMEWORK_SOURCES)
    return sources


def first_excerpt_id(fixture: SignalFixture, contains: str | None = None) -> str:
    if contains:
        for ex in fixture.excerpts:
            if contains.lower() in ex.excerpt.lower() or contains.lower() in ex.item.lower():
                return ex.source_id
    return fixture.excerpts[0].source_id


def signal_summary(fixture: SignalFixture) -> SignalSummary:
    if fixture.signal_kind == "both":
        headline = (
            f"{fixture.company.display_name}: non-reliance / restatement signal "
            f"with an ICFR material-weakness disclosure (DEMO)."
        )
    elif fixture.signal_kind == "restatement":
        headline = f"{fixture.company.display_name}: restatement / non-reliance signal (DEMO)."
    else:
        headline = (
            f"{fixture.company.display_name}: Item 9A-style material weakness "
            f"without a restatement to date (DEMO)."
        )
    return SignalSummary(
        fixture_id=fixture.fixture_id,
        signal_kind=fixture.signal_kind,
        forms=list(fixture.forms),
        filed_on=fixture.filed_on,
        period_end=fixture.period_end,
        headline=headline,
    )


def _claim(
    *,
    text: str,
    agent: str,
    step: str,
    source_ids: list[str],
    epistemic: str = "verified",
    confidence: str = "high",
) -> Claim:
    return Claim(
        text=text,
        epistemic=epistemic,  # type: ignore[arg-type]
        agent=agent,
        expansion_step=step,
        grounding_source_ids=source_ids,
        confidence=confidence,  # type: ignore[arg-type]
    )


def intake_claims(fixture: SignalFixture) -> list[Claim]:
    meta = f"meta-{fixture.fixture_id}"
    claims = [
        _claim(
            text=(
                f"{fixture.company.display_name} is a labeled DEMO issuer "
                f"({fixture.company.ticker}); this is not a real SEC registrant."
            ),
            agent="intake",
            step="expand:identity",
            source_ids=[meta],
        )
    ]
    if fixture.signal_kind in {"restatement", "both"}:
        sid = first_excerpt_id(fixture, "no longer be relied upon")
        claims.append(
            _claim(
                text=(
                    "Audit Committee concluded prior financial statements should "
                    f"no longer be relied upon ({fixture.structured_facts.get('restatement_periods', 'see excerpt')})."
                ),
                agent="intake",
                step="expand:item-4.02",
                source_ids=[sid],
            )
        )
    if fixture.signal_kind in {"material_weakness", "both"}:
        sid = first_excerpt_id(fixture, "material weakness")
        claims.append(
            _claim(
                text=(
                    "Management disclosed a material weakness in ICFR: "
                    f"{fixture.structured_facts.get('mw_area', 'see excerpt')}."
                ),
                agent="intake",
                step="expand:item-9a",
                source_ids=[sid],
            )
        )
    return claims


def why_now_pack(fixture: SignalFixture) -> WhyNow:
    meta = f"meta-{fixture.fixture_id}"
    triggers: list[Claim] = []
    if fixture.signal_kind in {"restatement", "both"}:
        triggers.append(
            _claim(
                text=(
                    "Why now: Item 4.02-style non-reliance starts an amendment "
                    "and investor-communication clock before the next periodic report."
                ),
                agent="why_now",
                step="compress:regulatory-clock",
                source_ids=[first_excerpt_id(fixture, "4.02"), meta],
            )
        )
        urgency = "immediate"
        clock = (
            "Immediate: non-reliance + restatement mechanics (amend prior periods, "
            "refresh 302/404 certifications, update Item 9A) before the next 10-Q/10-K."
        )
    else:
        triggers.append(
            _claim(
                text=(
                    "Why now: first disclosed MW in an annual ICFR opinion year "
                    "after a platform cutover; remediation evidence is needed for the next cycle."
                ),
                agent="why_now",
                step="compress:regulatory-clock",
                source_ids=[first_excerpt_id(fixture, "Item 9A"), meta],
                epistemic="inferred",
                confidence="medium",
            )
        )
        urgency = "this_quarter"
        clock = (
            "This quarter: design/operate ITGC remediation and IA testing so the "
            "next Item 9A can describe progress rather than an open MW."
        )
    extra = fixture.structured_facts.get("why_now")
    if extra:
        triggers.append(
            _claim(
                text=f"Fixture why-now fact: {extra}",
                agent="why_now",
                step="expand:fixture-fact",
                source_ids=[meta],
            )
        )
    return WhyNow(urgency=urgency, regulatory_clock=clock, triggers=triggers)  # type: ignore[arg-type]


def icfr_gaps(fixture: SignalFixture) -> list[ICFRGap]:
    areas = set(fixture.process_areas)
    gaps: list[ICFRGap] = []
    if "revenue_recognition" in areas:
        gaps.append(
            ICFRGap(
                coso_component=COSO["control_activities"],
                process="Revenue recognition / cutoff (ASC 606 bill-and-hold)",
                deficiency_type="both",
                severity="material_weakness",
                summary="Bill-and-hold criteria and cutoff were not tested before revenue was recorded.",
                claim=_claim(
                    text=(
                        "ICFR gap: design and operating failure over ASC 606 bill-and-hold "
                        "and revenue cutoff, allowing invoices to post before shipping-term and customer-request evidence was complete."
                    ),
                    agent="icfr",
                    step="expand:revenue-cutoff",
                    source_ids=[
                        first_excerpt_id(fixture, "bill-and-hold"),
                        first_excerpt_id(fixture, "material weakness"),
                    ],
                ),
                compensating_controls=[
                    "Quarterly detective review of aged bill-and-hold inventory (not designed to block recognition)."
                ],
            )
        )
    if "itgc_access" in areas or "change_management" in areas:
        gaps.append(
            ICFRGap(
                coso_component=COSO["control_activities"],
                process="ITGC — privileged access, SOD, change management",
                deficiency_type="both",
                severity="material_weakness",
                summary="Privileged and SOD-conflicting access plus unreviewed emergency changes over the payments ledger.",
                claim=_claim(
                    text=(
                        "ICFR gap: ITGCs over the payments ledger failed — lingering developer "
                        "production access, initiate/approve SOD conflicts, and emergency changes without independent review."
                    ),
                    agent="icfr",
                    step="expand:itgc",
                    source_ids=[
                        first_excerpt_id(fixture, "Privileged"),
                        first_excerpt_id(fixture, "Change-management"),
                    ],
                ),
                compensating_controls=[],
            )
        )
    if "inventory_reserves" in areas or "complex_estimates" in areas:
        gaps.append(
            ICFRGap(
                coso_component=COSO["risk_assessment"],
                process="Inventory existence and obsolescence / NRV reserves",
                deficiency_type="both",
                severity="material_weakness",
                summary="Obsolescence triggers and NRV estimates did not operate at period end.",
                claim=_claim(
                    text=(
                        "ICFR gap: inventory existence and obsolescence/NRV estimate controls "
                        "did not identify supplies approaching expiry carried above net realizable value."
                    ),
                    agent="icfr",
                    step="expand:inventory-nrv",
                    source_ids=[
                        first_excerpt_id(fixture, "net realizable"),
                        first_excerpt_id(fixture, "material weakness"),
                    ],
                ),
                compensating_controls=[],
            )
        )
    if "period_end_close" in areas:
        gaps.append(
            ICFRGap(
                coso_component=COSO["monitoring"],
                process="Period-end close / disclosure controls",
                deficiency_type="operating",
                severity="material_weakness",
                summary="Close and disclosure reviews did not escalate the error class into Item 9A / 4.02 in time.",
                claim=_claim(
                    text=(
                        "ICFR gap: period-end close and disclosure-control reviews did not "
                        "surface the error class in time to prevent a non-reliance or adverse ICFR conclusion."
                    ),
                    agent="icfr",
                    step="expand:close",
                    source_ids=[
                        first_excerpt_id(fixture, None),
                        "coso-icfr",
                    ],
                    epistemic="inferred",
                    confidence="medium",
                ),
                compensating_controls=[],
            )
        )
    return gaps


def buyer_seats(fixture: SignalFixture) -> list[BuyerSeat]:
    seats = [
        BuyerSeat(
            seat="CFO",
            raci="A",
            accountable_for="ICFR conclusion, 302/404 certifications, investor-facing restatement narrative",
            named_role="Chief Financial Officer",
            process_area="entity",
        ),
        BuyerSeat(
            seat="Audit Committee",
            raci="I",
            accountable_for="Oversight of non-reliance, MW remediation status, and external-auditor communications",
            named_role="Audit Committee Chair (oversight, not management)",
            process_area="governance",
        ),
        BuyerSeat(
            seat="Internal Audit",
            raci="R",
            accountable_for="Independent testing of remediated controls and evidence quality",
            named_role="Chief Audit Executive / SOX testing lead",
            process_area="assurance",
        ),
        BuyerSeat(
            seat="SOX PMO",
            raci="R",
            accountable_for="Control matrix, RCMs, deficiency tracking, and status to AC",
            named_role="SOX / ICFR program manager",
            process_area="program",
        ),
    ]
    areas = set(fixture.process_areas)
    if "revenue_recognition" in areas:
        seats.extend(
            [
                BuyerSeat(
                    seat="Controller",
                    raci="R",
                    accountable_for="ASC 606 policy, cutoff calendar, restatement journal entries",
                    named_role="Corporate Controller / CAO",
                    process_area="revenue_recognition",
                ),
                BuyerSeat(
                    seat="Process Owner",
                    raci="R",
                    accountable_for="Bill-and-hold evidence pack (customer request, shipping, ready-to-deliver)",
                    named_role="Revenue process owner (order-to-cash)",
                    process_area="revenue_recognition",
                ),
            ]
        )
    if "itgc_access" in areas or "change_management" in areas:
        seats.extend(
            [
                BuyerSeat(
                    seat="CIO/CISO",
                    raci="R",
                    accountable_for="Privileged access recertification, SOD, emergency-change review",
                    named_role="CIO / CISO (ITGC owner)",
                    process_area="itgc_access",
                ),
                BuyerSeat(
                    seat="Controller",
                    raci="C",
                    accountable_for="Business-side SOD and settlement-adjustment approval design",
                    named_role="Corporate Controller",
                    process_area="itgc_access",
                ),
            ]
        )
    if "inventory_reserves" in areas:
        seats.extend(
            [
                BuyerSeat(
                    seat="Controller",
                    raci="R",
                    accountable_for="NRV / obsolescence policy and restatement measurement",
                    named_role="Corporate Controller",
                    process_area="inventory_reserves",
                ),
                BuyerSeat(
                    seat="Process Owner",
                    raci="R",
                    accountable_for="Cycle counts, expiry reporting, and reserve trigger inputs",
                    named_role="Supply chain / clinic operations process owner",
                    process_area="inventory_reserves",
                ),
            ]
        )
    return seats


def next_actions(fixture: SignalFixture) -> list[NextAction]:
    actions: list[NextAction] = []
    areas = set(fixture.process_areas)
    if fixture.signal_kind in {"restatement", "both"}:
        actions.append(
            NextAction(
                owner_seat="Controller",
                action="Measure restatement entries for the non-reliance periods and draft the amended MD&A / footnote package.",
                due="10 business days",
                evidence_required="Restatement bridge, journal entries, and disclosure draft cross-referenced to excerpts",
                claim=_claim(
                    text="Next action: quantify restated periods and prepare the amendment package before the next periodic report.",
                    agent="ownership",
                    step="compress:actions",
                    source_ids=[first_excerpt_id(fixture, "no longer be relied upon"), "meshcfo-raci"],
                ),
            )
        )
    if "revenue_recognition" in areas:
        actions.append(
            NextAction(
                owner_seat="Process Owner",
                action="Re-perform ASC 606 bill-and-hold assessments for FY2025 Q2–Q3 and redesign the pre-recognition checklist.",
                due="15 business days",
                evidence_required="Customer-request letters, shipping hold evidence, ready-to-deliver checklist, and redesigned control narrative",
                claim=_claim(
                    text="Next action: rebuild bill-and-hold evidence and a preventive cutoff control before revenue posts.",
                    agent="ownership",
                    step="compress:actions",
                    source_ids=[first_excerpt_id(fixture, "bill-and-hold"), "meshcfo-raci"],
                ),
            )
        )
    if "itgc_access" in areas:
        actions.append(
            NextAction(
                owner_seat="CIO/CISO",
                action="Revoke leftover developer production access, recertify privileged users, and break initiate/approve SOD on settlement adjustments.",
                due="5 business days",
                evidence_required="Access recertification file, SOD exceptions closed, emergency-change review log",
                claim=_claim(
                    text="Next action: close ITGC access and SOD gaps created in the Q3 ledger cutover.",
                    agent="ownership",
                    step="compress:actions",
                    source_ids=[first_excerpt_id(fixture, "Privileged"), "meshcfo-raci"],
                ),
            )
        )
        actions.append(
            NextAction(
                owner_seat="Internal Audit",
                action="Test a population of emergency production changes and privileged-user activity since the cutover.",
                due="20 business days",
                evidence_required="IA workpapers with population, sample, exceptions, and residual-risk call",
                claim=_claim(
                    text="Next action: IA must independently test ITGC remediation — management assertion is not enough.",
                    agent="ownership",
                    step="compress:actions",
                    source_ids=[first_excerpt_id(fixture, "Change-management"), "meshcfo-raci"],
                ),
            )
        )
    if "inventory_reserves" in areas:
        actions.append(
            NextAction(
                owner_seat="Process Owner",
                action="Complete a wall-to-wall count of specialty supplies and apply expiry-based NRV triggers.",
                due="15 business days",
                evidence_required="Count sheets, expiry extract, NRV calculation, and reserve journal",
                claim=_claim(
                    text="Next action: re-measure inventory at NRV and install expiry triggers in the close calendar.",
                    agent="ownership",
                    step="compress:actions",
                    source_ids=[first_excerpt_id(fixture, "net realizable"), "meshcfo-raci"],
                ),
            )
        )
    actions.append(
        NextAction(
            owner_seat="CFO",
            action="Refresh SOX 302/404 certification package and the Audit Committee MW/restatement status memo.",
            due="This reporting cycle",
            evidence_required="Updated sub-certifications, Item 9A draft, AC minutes placeholder",
            claim=_claim(
                text="Next action: CFO owns the certification and AC narrative; this is not delegated advice.",
                agent="ownership",
                step="compress:actions",
                source_ids=["meshcfo-raci", f"meta-{fixture.fixture_id}"],
            ),
        )
    )
    return actions


def foundation_facts(fixture: SignalFixture) -> list[str]:
    facts = [
        fixture.demo_disclaimer,
        f"Forms in fixture: {', '.join(fixture.forms)} filed_on={fixture.filed_on} period_end={fixture.period_end}.",
    ]
    facts.extend(f"{key}: {value}" for key, value in fixture.structured_facts.items())
    return facts


def default_attacks(fixture: SignalFixture) -> list[str]:
    attacks = [
        "Do not treat DEMO excerpts as facts about any real registrant.",
        "Compensating controls mentioned in filings are often detective-only and do not reduce a MW to a SD without evidence.",
        "Management 'has not identified a restatement to date' is not evidence that the control is effective.",
    ]
    if "revenue_recognition" in fixture.process_areas:
        attacks.append(
            "Bill-and-hold restatements are frequently incomplete if only invoices are reversed and channel inventory is not re-tested."
        )
    if "itgc_access" in fixture.process_areas:
        attacks.append(
            "Access recertification without a joiner/mover/leaver redesign typically re-opens the MW next period."
        )
    return attacks


def pipeline_seed() -> list[PipelineEvent]:
    return []
