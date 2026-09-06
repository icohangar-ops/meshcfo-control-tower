# Spec: remediation-briefs

## ADDED Requirements

### Requirement: Governed brief from an EDGAR-style signal

The system SHALL produce a structured remediation brief from a labeled DEMO
material-weakness or restatement signal. The brief SHALL include why-now,
buyer seats, ICFR gaps, next actions, and a complete claim list.

#### Scenario: Northstar demo fixture

- **WHEN** the operator selects the `northstar` DEMO fixture
- **THEN** the system returns a brief with `demo=true`, company ticker
  `NSMT-DEMO`, at least one restatement why-now trigger, and at least one
  revenue-related ICFR gap

### Requirement: Per-claim provenance

Every claim in the brief SHALL name the producing agent, an expansion step,
an epistemic tag, and one or more grounding source IDs that exist in the
source registry.

#### Scenario: R0 drops an ungrounded claim

- **WHEN** a claim has no grounding source IDs or an unknown source ID
- **THEN** the R0 gate SHALL exclude that claim from the locked artifact
  and record a CHP finding

### Requirement: MeshCFO ownership, not free-form advice

Each ICFR gap SHALL map to one or more buyer seats with a RACI code. Next
actions SHALL name an owner seat and the evidence required to close.

#### Scenario: Revenue cutoff material weakness

- **WHEN** the signal describes a revenue cutoff / bill-and-hold material weakness
- **THEN** the brief SHALL assign Controller or Process Owner as Responsible
  and CFO as Accountable

### Requirement: NVIDIA Nemotron on Nebius Token Factory

Live synthesis SHALL call the OpenAI-compatible Token Factory API at
`https://api.tokenfactory.nebius.com/v1/` using `NEBIUS_API_KEY` and prefer
`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`.

#### Scenario: Missing API key

- **WHEN** `NEBIUS_API_KEY` is unset and offline mode is requested
- **THEN** the system SHALL emit a deterministic brief from the fixture
  playbook and mark `model.mode` as `offline`

### Requirement: Demo fixtures are labeled DEMO

Fixture issuers SHALL be fictional and explicitly labeled DEMO. The brief
SHALL not present them as real SEC registrants.

#### Scenario: Fixture banner

- **WHEN** a fixture is loaded
- **THEN** `company.demo` is true and the display name contains `(DEMO)`
