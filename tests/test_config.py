from datetime import date

import pytest

from releaseclock.config import PlanValidationError, load_plan


def test_loads_a_declared_release_campaign_without_inventing_milestones(tmp_path):
    """The loader must retain the artist-authored plan rather than add a template."""
    plan_path = tmp_path / "campaign.toml"
    plan_path.write_text(
        """
[release]
artist = "Example Artist"
title = "Example Release"
release_date = "2026-01-05"
timezone = "Europe/Berlin"
requirements_basis = "Provisional internal campaign plan; confirm every external action manually."

[[milestones]]
id = "metadata"
offset_days = -42
title = "Lock the declared metadata sheet"
owner = "Artist"
status = "planned"
critical = true
evidence_next_step = "Read back the current local metadata sheet."
notes = "No upload or platform action is implied."

[[milestones]]
id = "review"
offset_days = 14
title = "Write a post-release review"
owner = "Label"
status = "planned"
critical = false
evidence_next_step = "Collect the evidence that matters to this release."
""".lstrip(),
        encoding="utf-8",
    )

    plan = load_plan(plan_path)

    assert plan.artist == "Example Artist"
    assert plan.title == "Example Release"
    assert plan.release_date == date(2026, 1, 5)
    assert plan.timezone == "Europe/Berlin"
    assert plan.requirements_basis.startswith("Provisional internal")
    assert [milestone.identifier for milestone in plan.milestones] == [
        "metadata",
        "review",
    ]
    assert plan.milestones[0].notes == "No upload or platform action is implied."


def test_rejects_ids_that_collide_after_case_and_whitespace_normalization(tmp_path):
    """Two visually similar IDs would make a checklist impossible to audit."""
    plan_path = tmp_path / "campaign.toml"
    plan_path.write_text(
        """
[release]
artist = "Example Artist"
title = "Example Release"
release_date = "2026-01-05"
requirements_basis = "Provisional internal campaign plan."

[[milestones]]
id = "Promo List"
offset_days = -7
title = "Prepare list"
owner = "Artist"
status = "planned"
critical = false
evidence_next_step = "Read the list."

[[milestones]]
id = " promo   list "
offset_days = -1
title = "Review list"
owner = "Label"
status = "planned"
critical = false
evidence_next_step = "Read the review note."
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(PlanValidationError, match="duplicate"):
        load_plan(plan_path)


@pytest.mark.parametrize(
    ("needle", "replacement", "error_match"),
    [
        ('timezone = "Europe/Berlin"', 'timezone = "Mars/Olympus"', "timezone"),
        ('status = "planned"', 'status = "complete"', "status"),
    ],
)
def test_rejects_unrecognized_timezones_and_statuses(
    tmp_path, needle, replacement, error_match
):
    """Unknown campaign facts must not silently produce an importable calendar."""
    contents = """
[release]
artist = "Example Artist"
title = "Example Release"
release_date = "2026-01-05"
timezone = "Europe/Berlin"
requirements_basis = "Provisional internal campaign plan."

[[milestones]]
id = "metadata"
offset_days = -7
title = "Lock the declared metadata sheet"
owner = "Artist"
status = "planned"
critical = true
evidence_next_step = "Read the current metadata sheet."
""".lstrip()
    plan_path = tmp_path / "campaign.toml"
    plan_path.write_text(contents.replace(needle, replacement), encoding="utf-8")

    with pytest.raises(PlanValidationError, match=error_match):
        load_plan(plan_path)
