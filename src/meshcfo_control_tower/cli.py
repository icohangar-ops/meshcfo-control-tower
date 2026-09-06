"""CLI: print a JSON remediation brief."""

from __future__ import annotations

import argparse
import json
import sys

from meshcfo_control_tower.catalog import list_fixtures
from meshcfo_control_tower.pipeline import run_brief


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="meshcfo-brief",
        description=(
            "Cubiczan MeshCFO Control Tower — emit a governed ICFR remediation "
            "brief as JSON. Powered by NVIDIA Nemotron on Nebius Token Factory."
        ),
    )
    parser.add_argument(
        "--fixture",
        default="northstar",
        help="DEMO fixture id: northstar | lumenbridge | cedarline",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip Token Factory and use deterministic playbooks only",
    )
    parser.add_argument(
        "--no-market",
        action="store_true",
        help="Do not call Tavily even if TAVILY_API_KEY is set",
    )
    parser.add_argument(
        "--lock-validator",
        default=None,
        help="Optional named validator to advance PROVISIONAL_LOCK → LOCKED",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_fixtures",
        help="List DEMO fixtures and exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_fixtures:
        print(json.dumps(list_fixtures(), indent=2))
        return 0
    try:
        brief = run_brief(
            args.fixture,
            offline=args.offline,
            use_market=not args.no_market,
            lock_validator=args.lock_validator,
        )
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(brief.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
