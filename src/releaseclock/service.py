"""One stable campaign assessment from a declared local plan."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .config import CampaignPlan, load_plan_bytes
from .core import ScheduledMilestone, schedule_milestones

DECLARED_CAMPAIGN_STATUS = (
    "DECLARED CAMPAIGN PLAN - EXTERNAL SCHEDULING, CONTENT, OUTREACH, "
    "AND PUBLICATION STATUS UNVERIFIED"
)


@dataclass(frozen=True)
class CampaignAssessment:
    plan: CampaignPlan
    scheduled: tuple[ScheduledMilestone, ...]
    plan_sha256: str
    status: str = DECLARED_CAMPAIGN_STATUS


def assess(plan_path: Path) -> CampaignAssessment:
    """Load one plan and derive its declared milestone dates."""
    plan_bytes = plan_path.read_bytes()
    plan = load_plan_bytes(plan_bytes)
    return CampaignAssessment(
        plan=plan,
        scheduled=schedule_milestones(
            release_date=plan.release_date,
            milestones=list(plan.milestones),
        ),
        plan_sha256=hashlib.sha256(plan_bytes).hexdigest(),
    )
