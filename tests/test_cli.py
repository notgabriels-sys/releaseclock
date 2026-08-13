import json

from releaseclock.cli import main


def test_check_emits_a_path_free_declared_campaign_result_without_writing(
    tmp_path, capsys
):
    """Checking a plan must not create a calendar or imply an external action."""
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

    code = main(["check", str(plan_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["status"].startswith("DECLARED CAMPAIGN PLAN")
    assert payload["milestones"][0]["scheduled_date"] == "2025-12-29"
    assert payload["unverified"][0].startswith("calendar import")
    assert str(tmp_path) not in json.dumps(payload)
    assert not (tmp_path / "campaign-bundle").exists()


def test_build_emits_only_artifact_names_in_json(tmp_path, capsys):
    """A machine-readable build result must not disclose its local output path."""
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
    output = tmp_path / "campaign-bundle"

    code = main(["build", str(plan_path), "--output", str(output), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["artifacts"] == [
        "CAMPAIGN_TIMELINE.md",
        "campaign_milestones.csv",
        "CAMPAIGN.ics",
        "manifest.json",
    ]
    assert str(output) not in json.dumps(payload)
    assert output.joinpath("CAMPAIGN.ics").is_file()
