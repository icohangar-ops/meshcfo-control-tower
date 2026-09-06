# Spec: remediation-briefs

The system produces a structured remediation brief from a labeled DEMO
material-weakness or restatement signal. The brief includes why-now, buyer
seats, ICFR gaps, next actions, and a complete claim list with R0 provenance.

Live synthesis calls Nebius Token Factory at
`https://api.tokenfactory.nebius.com/v1/` using `NEBIUS_API_KEY` and prefers
`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`. Fixture issuers are fictional and
labeled DEMO.
