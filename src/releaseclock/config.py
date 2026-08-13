"""Typed parsing for a declared release-campaign plan."""

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .core import Milestone

ALLOWED_STATUSES = {"planned", "in_progress", "blocked", "declared_done"}


class PlanValidationError(ValueError):
    """A user-authored campaign plan is incomplete or ambiguous."""


@dataclass(frozen=True)
class CampaignPlan:
    artist: str
    title: str
    release_date: date
    timezone: str | None
    requirements_basis: str
    milestones: tuple[Milestone, ...]


def load_plan(path: Path) -> CampaignPlan:
    """Load one local, owner-declared campaign plan from TOML."""
    return load_plan_bytes(path.read_bytes())


def load_plan_bytes(contents: bytes) -> CampaignPlan:
    """Load a plan from exact TOML bytes so callers can retain a source fingerprint."""
    try:
        data = tomllib.loads(contents.decode("utf-8"))
    except UnicodeDecodeError as error:
        raise PlanValidationError("plan must be UTF-8 encoded TOML") from error
    release = _section(data, "release")
    milestones_data = data.get("milestones")
    if not isinstance(milestones_data, list) or not milestones_data:
        raise PlanValidationError("milestones must contain at least one TOML table")
    milestones = tuple(
        _milestone(item, index) for index, item in enumerate(milestones_data)
    )
    _reject_duplicate_identifiers(milestones)
    return CampaignPlan(
        artist=_non_empty_string(release, "artist", "release.artist"),
        title=_non_empty_string(release, "title", "release.title"),
        release_date=_date(release, "release_date", "release.release_date"),
        timezone=_timezone(release),
        requirements_basis=_non_empty_string(
            release, "requirements_basis", "release.requirements_basis"
        ),
        milestones=milestones,
    )


def _milestone(item: Any, index: int) -> Milestone:
    name = f"milestones[{index}]"
    if not isinstance(item, dict):
        raise PlanValidationError(f"{name} must be a TOML table")
    status = _non_empty_string(item, "status", f"{name}.status")
    if status not in ALLOWED_STATUSES:
        choices = ", ".join(sorted(ALLOWED_STATUSES))
        raise PlanValidationError(f"{name}.status must be one of {choices}")
    return Milestone(
        identifier=_non_empty_string(item, "id", f"{name}.id"),
        offset_days=_integer(item, "offset_days", f"{name}.offset_days"),
        title=_non_empty_string(item, "title", f"{name}.title"),
        owner=_non_empty_string(item, "owner", f"{name}.owner"),
        status=status,
        critical=_boolean(item, "critical", f"{name}.critical"),
        evidence_next_step=_non_empty_string(
            item, "evidence_next_step", f"{name}.evidence_next_step"
        ),
        notes=_optional_string(item, "notes", f"{name}.notes"),
    )


def _reject_duplicate_identifiers(milestones: tuple[Milestone, ...]) -> None:
    identifiers: set[str] = set()
    for milestone in milestones:
        normalized = _normalized_identifier(milestone.identifier)
        if normalized in identifiers:
            raise PlanValidationError(
                "milestones contain duplicate ids after normalization"
            )
        identifiers.add(normalized)


def _normalized_identifier(value: str) -> str:
    return " ".join(value.split()).casefold()


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise PlanValidationError(f"{name} must be a TOML table")
    return value


def _required(section: dict[str, Any], key: str, name: str) -> Any:
    if key not in section:
        raise PlanValidationError(f"{name} is required")
    return section[key]


def _non_empty_string(section: dict[str, Any], key: str, name: str) -> str:
    value = _required(section, key, name)
    if not isinstance(value, str) or not value.strip():
        raise PlanValidationError(f"{name} must be a non-empty string")
    return value.strip()


def _optional_string(section: dict[str, Any], key: str, name: str) -> str:
    if key not in section:
        return ""
    value = section[key]
    if not isinstance(value, str):
        raise PlanValidationError(f"{name} must be a string")
    return value.strip()


def _integer(section: dict[str, Any], key: str, name: str) -> int:
    value = _required(section, key, name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise PlanValidationError(f"{name} must be an integer")
    return value


def _boolean(section: dict[str, Any], key: str, name: str) -> bool:
    value = _required(section, key, name)
    if not isinstance(value, bool):
        raise PlanValidationError(f"{name} must be true or false")
    return value


def _date(section: dict[str, Any], key: str, name: str) -> date:
    value = _non_empty_string(section, key, name)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise PlanValidationError(f"{name} must be an ISO date") from error


def _timezone(section: dict[str, Any]) -> str | None:
    if "timezone" not in section:
        return None
    value = _non_empty_string(section, "timezone", "release.timezone")
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as error:
        raise PlanValidationError(
            "release.timezone must be an IANA timezone"
        ) from error
    return value
