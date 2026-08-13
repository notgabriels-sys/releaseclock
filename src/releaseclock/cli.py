"""Command-line interface for declared release-campaign plans."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .report import BundleFiles, write_bundle
from .service import CampaignAssessment, assess


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="releaseclock",
        description="Build a local timeline from owner-declared release campaign milestones.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "build"):
        subparser = subcommands.add_parser(command)
        subparser.add_argument(
            "plan", type=Path, help="Path to a releaseclock TOML plan"
        )
        subparser.add_argument(
            "--json",
            action="store_true",
            help="Print a path-free machine-readable result",
        )
        if command == "build":
            subparser.add_argument(
                "--output",
                required=True,
                type=Path,
                help="New directory for the local timeline, CSV, calendar, and manifest",
            )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Check or explicitly build a local campaign bundle."""
    args = build_parser().parse_args(argv)
    try:
        assessment = assess(args.plan)
        files: BundleFiles | None = None
        if args.command == "build":
            files = write_bundle(assessment=assessment, output_dir=args.output)
    except (KeyError, OSError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1

    if args.json:
        payload = _as_json(assessment)
        if files:
            payload["artifacts"] = [
                files.timeline_path.name,
                files.milestones_path.name,
                files.calendar_path.name,
                files.manifest_path.name,
            ]
        print(json.dumps(payload, sort_keys=True))
    else:
        if files:
            print(f"Built {files.timeline_path}")
            print(f"Built {files.milestones_path}")
            print(f"Built {files.calendar_path}")
            print(f"Built {files.manifest_path}")
        _print_summary(assessment)
    return 0


def _print_summary(assessment: CampaignAssessment) -> None:
    print(assessment.status)
    print(
        f"Declared release: {assessment.plan.artist} — {assessment.plan.title} "
        f"({assessment.plan.release_date.isoformat()})"
    )
    for milestone in assessment.scheduled:
        print(
            f"{milestone.scheduled_date.isoformat()} {milestone.identifier} "
            f"status={milestone.status} owner={milestone.owner}"
        )
    print(
        "Calendar import, task scheduling, content, outreach, and publication remain unverified."
    )


def _as_json(assessment: CampaignAssessment) -> dict[str, object]:
    return {
        "status": assessment.status,
        "release": {
            "artist": assessment.plan.artist,
            "title": assessment.plan.title,
            "release_date": assessment.plan.release_date.isoformat(),
            "timezone": assessment.plan.timezone,
            "requirements_basis": assessment.plan.requirements_basis,
        },
        "milestones": [
            {
                "id": milestone.identifier,
                "scheduled_date": milestone.scheduled_date.isoformat(),
                "offset_days": milestone.offset_days,
                "title": milestone.title,
                "owner": milestone.owner,
                "declared_status": milestone.status,
                "critical": milestone.critical,
                "evidence_next_step": milestone.evidence_next_step,
                "notes": milestone.notes,
            }
            for milestone in assessment.scheduled
        ],
        "unverified": [
            "calendar import and task scheduling are not verified",
            "content creation, outreach, and recipient response are not verified",
            "upload, publication, public availability, and campaign outcomes are not verified",
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
