"""Pure scheduling for owner-declared campaign milestones."""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class Milestone:
    identifier: str
    offset_days: int
    title: str
    owner: str
    status: str
    critical: bool
    evidence_next_step: str
    notes: str = ""


@dataclass(frozen=True)
class ScheduledMilestone:
    identifier: str
    offset_days: int
    scheduled_date: date
    title: str
    owner: str
    status: str
    critical: bool
    evidence_next_step: str
    notes: str = ""


def schedule_milestones(
    *, release_date: date, milestones: list[Milestone]
) -> tuple[ScheduledMilestone, ...]:
    """Apply each declared day offset and return a stable chronological schedule."""
    scheduled = [
        ScheduledMilestone(
            identifier=milestone.identifier,
            offset_days=milestone.offset_days,
            scheduled_date=release_date + timedelta(days=milestone.offset_days),
            title=milestone.title,
            owner=milestone.owner,
            status=milestone.status,
            critical=milestone.critical,
            evidence_next_step=milestone.evidence_next_step,
            notes=milestone.notes,
        )
        for milestone in milestones
    ]
    return tuple(
        sorted(
            scheduled,
            key=lambda milestone: (
                milestone.scheduled_date,
                milestone.offset_days,
                milestone.identifier.casefold(),
            ),
        )
    )
