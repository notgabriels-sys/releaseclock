"""Portable local artifacts for a declared campaign plan."""

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from .service import CampaignAssessment


@dataclass(frozen=True)
class BundleFiles:
    timeline_path: Path
    milestones_path: Path
    calendar_path: Path
    manifest_path: Path


def write_bundle(*, assessment: CampaignAssessment, output_dir: Path) -> BundleFiles:
    """Write one new local bundle without touching the source plan or a calendar service."""
    if output_dir.exists():
        raise ValueError("output_dir must not already exist")
    if not output_dir.parent.is_dir():
        raise ValueError("output_dir parent must be an existing directory")
    output_dir.mkdir()

    timeline_path = output_dir / "CAMPAIGN_TIMELINE.md"
    milestones_path = output_dir / "campaign_milestones.csv"
    calendar_path = output_dir / "CAMPAIGN.ics"
    manifest_path = output_dir / "manifest.json"

    _write_timeline(assessment, timeline_path)
    _write_milestones_csv(assessment, milestones_path)
    _write_calendar(assessment, calendar_path)
    _write_manifest(
        assessment,
        manifest_path,
        (timeline_path, milestones_path, calendar_path),
    )
    return BundleFiles(
        timeline_path=timeline_path,
        milestones_path=milestones_path,
        calendar_path=calendar_path,
        manifest_path=manifest_path,
    )


def _write_timeline(assessment: CampaignAssessment, path: Path) -> None:
    plan = assessment.plan
    lines = [
        "# Declared campaign timeline",
        "",
        "## Boundary",
        "",
        f"`{assessment.status}`",
        "",
        (
            "This local plan does not establish that any calendar was imported, any task was "
            "scheduled, any content was made, any outreach was sent, or any release was published. "
            "Every milestone status below is author-declared and needs separate evidence."
        ),
        "",
        "## Release context",
        "",
        f"- Artist: {plan.artist}",
        f"- Title: {plan.title}",
        f"- Declared release date: {plan.release_date.isoformat()}",
        f"- Timezone label: {plan.timezone or 'Not declared'}",
        f"- Requirements basis: {plan.requirements_basis}",
        "",
        "## Milestones",
        "",
        "| Date | Offset | ID | Title | Owner | Declared status | Critical |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for milestone in assessment.scheduled:
        lines.append(
            "| "
            f"{milestone.scheduled_date.isoformat()} | {_format_offset(milestone.offset_days)} | "
            f"{milestone.identifier} | {milestone.title} | {milestone.owner} | "
            f"{milestone.status} | {'yes' if milestone.critical else 'no'} |"
        )
    lines.extend(["", "## Manual evidence gates", ""])
    for milestone in assessment.scheduled:
        lines.extend(
            [
                f"### {milestone.scheduled_date.isoformat()} — {milestone.identifier}",
                "",
                f"- Declared status: `{milestone.status}` (not independently verified)",
                f"- Owner: {milestone.owner}",
                f"- Critical: {'yes' if milestone.critical else 'no'}",
                f"- Next evidence to obtain: {milestone.evidence_next_step}",
            ]
        )
        if milestone.notes:
            lines.append(f"- Notes: {milestone.notes}")
        lines.append("")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_milestones_csv(assessment: CampaignAssessment, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "scheduled_date",
                "offset_days",
                "id",
                "title",
                "owner",
                "declared_status",
                "critical",
                "evidence_next_step",
                "notes",
            ]
        )
        for milestone in assessment.scheduled:
            writer.writerow(
                [
                    milestone.scheduled_date.isoformat(),
                    milestone.offset_days,
                    milestone.identifier,
                    milestone.title,
                    milestone.owner,
                    milestone.status,
                    str(milestone.critical).lower(),
                    milestone.evidence_next_step,
                    milestone.notes,
                ]
            )


def _write_calendar(assessment: CampaignAssessment, path: Path) -> None:
    plan = assessment.plan
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//releaseclock//Declared Campaign Plan//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_escape_ical_text(f'{plan.artist}: {plan.title} campaign')}",
    ]
    if plan.timezone:
        lines.append(f"X-WR-TIMEZONE:{_escape_ical_text(plan.timezone)}")
    for milestone in assessment.scheduled:
        end_date = milestone.scheduled_date + timedelta(days=1)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_event_uid(assessment, milestone.identifier, milestone.scheduled_date.isoformat())}",
                f"DTSTAMP:{plan.release_date.strftime('%Y%m%d')}T000000Z",
                f"DTSTART;VALUE=DATE:{milestone.scheduled_date.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{end_date.strftime('%Y%m%d')}",
                f"SUMMARY:{_escape_ical_text(f'{plan.title}: {milestone.title}')}",
                f"DESCRIPTION:{_escape_ical_text(_event_description(assessment, milestone.identifier))}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    path.write_bytes(_ical_bytes(lines))


def _event_uid(
    assessment: CampaignAssessment, identifier: str, scheduled_date: str
) -> str:
    plan = assessment.plan
    seed = (
        f"{plan.artist}\x00{plan.title}\x00{plan.release_date.isoformat()}\x00"
        f"{identifier}\x00{scheduled_date}"
    )
    return f"{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:32]}@releaseclock.local"


def _event_description(assessment: CampaignAssessment, identifier: str) -> str:
    milestone = next(
        item for item in assessment.scheduled if item.identifier == identifier
    )
    lines = [
        "Declared campaign milestone only.",
        f"Declared status: {milestone.status} (not independently verified).",
        f"Owner: {milestone.owner}",
        f"Critical: {'yes' if milestone.critical else 'no'}",
        f"Next evidence to obtain: {milestone.evidence_next_step}",
        "This does not confirm scheduling, outreach, content, or publication.",
    ]
    if milestone.notes:
        lines.insert(-1, f"Notes: {milestone.notes}")
    return "\n".join(lines)


def _escape_ical_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
    )


def _ical_bytes(lines: list[str]) -> bytes:
    folded_lines: list[str] = []
    for line in lines:
        folded_lines.extend(_fold_ical_line(line))
    return ("\r\n".join(folded_lines) + "\r\n").encode("utf-8")


def _fold_ical_line(line: str) -> list[str]:
    """Fold iCalendar content lines at 75 octets without splitting Unicode characters."""
    segments: list[str] = []
    current = ""
    current_bytes = 0
    limit = 75
    for character in line:
        character_bytes = len(character.encode("utf-8"))
        if current and current_bytes + character_bytes > limit:
            segments.append(current)
            current = f" {character}"
            current_bytes = 1 + character_bytes
        else:
            current += character
            current_bytes += character_bytes
    segments.append(current)
    return segments


def _write_manifest(
    assessment: CampaignAssessment,
    path: Path,
    artifacts: tuple[Path, Path, Path],
) -> None:
    payload = {
        "status": assessment.status,
        "release": {
            "artist": assessment.plan.artist,
            "title": assessment.plan.title,
            "release_date": assessment.plan.release_date.isoformat(),
            "timezone": assessment.plan.timezone,
            "requirements_basis": assessment.plan.requirements_basis,
        },
        "plan_sha256": assessment.plan_sha256,
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
        "artifacts": [artifact.name for artifact in artifacts],
        "artifact_sha256": {
            artifact.name: hashlib.sha256(artifact.read_bytes()).hexdigest()
            for artifact in artifacts
        },
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _format_offset(offset_days: int) -> str:
    return f"+{offset_days}" if offset_days > 0 else str(offset_days)
