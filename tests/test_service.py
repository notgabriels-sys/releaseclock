from datetime import date

from releaseclock.service import assess


def test_assessment_keeps_the_plan_and_derived_dates_under_an_explicit_boundary(
    tmp_path,
):
    """A local timeline must never be labelled as an executed campaign."""
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

    assessment = assess(plan_path)

    assert assessment.status == (
        "DECLARED CAMPAIGN PLAN - EXTERNAL SCHEDULING, CONTENT, OUTREACH, "
        "AND PUBLICATION STATUS UNVERIFIED"
    )
    assert assessment.plan.title == "Example Release"
    assert assessment.scheduled[0].scheduled_date == date(2025, 12, 29)
