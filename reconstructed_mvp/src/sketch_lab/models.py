from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Lab(StrEnum):
    REFERENCE_IDEA = "reference_idea"
    PEOPLE_ANATOMY_ANIMALS = "people_anatomy_animals"
    PERSPECTIVE_ENVIRONMENTS = "perspective_environments"
    MACHINES_IN_MOTION = "machines_in_motion"
    LIGHTING_VALUES = "lighting_values"
    OPEN_KITCHEN = "open_kitchen"


class EvidenceLabel(StrEnum):
    RETRIEVED_FACT = "retrieved_fact"
    DIRECT_OBSERVATION = "direct_observation"
    EXTERNAL_SOURCE = "external_source"
    INFERENCE = "inference"
    PROPOSAL = "proposal"
    UNKNOWN = "unknown"


class ApprovalLevel(StrEnum):
    AUTO = "AUTO"
    CONFIRM = "CONFIRM"
    EXPLICIT = "EXPLICIT"


@dataclass(slots=True)
class Artwork:
    artwork_id: str
    project_id: str
    title: str
    primary_lab: str
    supporting_labs: list[str] = field(default_factory=list)
    status: str = "active"
    current_goal: str = ""
    constraints: list[str] = field(default_factory=list)
    next_action: str = ""
    version: int = 1
    updated_at: str = field(default_factory=utc_now)

    def payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RouteDecision:
    primary_lab: str
    consultants: list[str]
    reasons: dict[str, str]
    requires_human_confirmation: bool = False


@dataclass(slots=True)
class RunResult:
    run_id: str
    artwork_id: str
    state_version: int
    route: RouteDecision
    findings: list[dict[str, Any]]
    disagreements: list[dict[str, Any]]
    recommendation: str
    approval_required: bool

