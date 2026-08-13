from datetime import date

from releaseclock.core import Milestone, schedule_milestones


def test_derives_and_orders_dates_from_signed_offsets_across_a_year_boundary():
    """A reversed sign or unordered calendar would make the schedule misleading."""
    scheduled = schedule_milestones(
        release_date=date(2026, 1, 5),
        milestones=[
            Milestone(
                identifier="follow-up",
                offset_days=14,
                title="Review declared outcomes",
                owner="Label",
                status="planned",
                critical=False,
                evidence_next_step="Write a review note.",
            ),
            Milestone(
                identifier="metadata",
                offset_days=-7,
                title="Lock metadata sheet",
                owner="Artist",
                status="planned",
                critical=True,
                evidence_next_step="Read the current metadata sheet.",
            ),
            Milestone(
                identifier="release-day",
                offset_days=0,
                title="Review release-day actions",
                owner="Label",
                status="planned",
                critical=True,
                evidence_next_step="Confirm each action manually.",
            ),
        ],
    )

    assert [item.identifier for item in scheduled] == [
        "metadata",
        "release-day",
        "follow-up",
    ]
    assert [item.scheduled_date for item in scheduled] == [
        date(2025, 12, 29),
        date(2026, 1, 5),
        date(2026, 1, 19),
    ]


def test_uses_identifier_order_when_multiple_milestones_share_a_date():
    """Same-day records must still produce a stable review and calendar order."""
    scheduled = schedule_milestones(
        release_date=date(2026, 1, 5),
        milestones=[
            Milestone(
                identifier="zeta",
                offset_days=0,
                title="Later alphabetically",
                owner="Artist",
                status="planned",
                critical=False,
                evidence_next_step="Review the declared task.",
            ),
            Milestone(
                identifier="alpha",
                offset_days=0,
                title="Earlier alphabetically",
                owner="Artist",
                status="planned",
                critical=False,
                evidence_next_step="Review the declared task.",
            ),
        ],
    )

    assert [item.identifier for item in scheduled] == ["alpha", "zeta"]
