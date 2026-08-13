import csv
import hashlib
import json

import pytest

from releaseclock.report import write_bundle
from releaseclock.service import assess


def test_writes_a_portable_timeline_csv_calendar_and_manifest(tmp_path):
    """A built plan must expose dates and remain clear that nothing was executed."""
    plan_path = tmp_path / "campaign.toml"
    plan_path.write_text(
        """
[release]
artist = "Example Artist"
title = "Example Release"
release_date = "2026-01-05"
timezone = "Europe/Berlin"
requirements_basis = "Provisional internal campaign plan."

[[milestones]]
id = "metadata"
offset_days = -7
title = "Lock metadata, credits; artwork notes"
owner = "Artist"
status = "planned"
critical = true
evidence_next_step = "Read the current metadata sheet."
notes = "No platform action is implied."
""".lstrip(),
        encoding="utf-8",
    )
    assessment = assess(plan_path)

    output = tmp_path / "campaign-bundle"
    files = write_bundle(assessment=assessment, output_dir=output)

    timeline = files.timeline_path.read_text(encoding="utf-8")
    assert files.timeline_path.name == "CAMPAIGN_TIMELINE.md"
    assert files.milestones_path.name == "campaign_milestones.csv"
    assert files.calendar_path.name == "CAMPAIGN.ics"
    assert files.manifest_path.name == "manifest.json"
    assert "DECLARED CAMPAIGN PLAN - EXTERNAL SCHEDULING" in timeline
    assert "2025-12-29" in timeline
    assert "does not establish that any calendar was imported" in timeline

    with files.milestones_path.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["scheduled_date"] == "2025-12-29"
    assert row["critical"] == "true"
    assert row["declared_status"] == "planned"

    calendar = files.calendar_path.read_bytes()
    assert calendar.startswith(b"BEGIN:VCALENDAR\r\n")
    assert b"DTSTART;VALUE=DATE:20251229\r\n" in calendar
    assert (
        b"SUMMARY:Example Release: Lock metadata\\, credits\\; artwork notes\r\n"
        in calendar
    )
    assert b"END:VCALENDAR\r\n" in calendar
    assert all(len(line) <= 75 for line in calendar.split(b"\r\n") if line)

    manifest = json.loads(files.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == assessment.status
    assert manifest["artifacts"] == [
        "CAMPAIGN_TIMELINE.md",
        "campaign_milestones.csv",
        "CAMPAIGN.ics",
    ]
    assert (
        manifest["artifact_sha256"]["CAMPAIGN.ics"]
        == hashlib.sha256(files.calendar_path.read_bytes()).hexdigest()
    )
    assert manifest["plan_sha256"] == hashlib.sha256(plan_path.read_bytes()).hexdigest()
    assert str(tmp_path) not in json.dumps(manifest)


def test_refuses_to_replace_an_existing_output_directory(tmp_path):
    """An existing bundle might be a reviewed record and must remain untouched."""
    plan_path = tmp_path / "campaign.toml"
    plan_path.write_text(
        """
[release]
artist = "Example Artist"
title = "Example Release"
release_date = "2026-01-05"
requirements_basis = "Provisional internal campaign plan."

[[milestones]]
id = "metadata"
offset_days = -7
title = "Lock the declared metadata sheet"
owner = "Artist"
status = "planned"
critical = true
evidence_next_step = "Read the current metadata sheet."
""".lstrip(),
        encoding="utf-8",
    )
    output = tmp_path / "existing-bundle"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("do not replace", encoding="utf-8")

    with pytest.raises(ValueError, match="must not already exist"):
        write_bundle(assessment=assess(plan_path), output_dir=output)

    assert sentinel.read_text(encoding="utf-8") == "do not replace"
