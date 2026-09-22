from __future__ import annotations

import hashlib
from typing import Iterable

from .ledger import Ledger
from .models import Lab, RouteDecision, RunResult


LAB_KEYWORDS: dict[str, set[str]] = {
    Lab.PERSPECTIVE_ENVIRONMENTS: {"perspective", "depth", "environment", "architecture", "horizon", "map", "lighthouse"},
    Lab.LIGHTING_VALUES: {"light", "lighting", "shadow", "value", "contrast", "reflection", "glow"},
    Lab.MACHINES_IN_MOTION: {"car", "vehicle", "wheel", "machine", "aircraft", "nova", "racing"},
    Lab.PEOPLE_ANATOMY_ANIMALS: {"person", "anatomy", "animal", "face", "hand", "wing", "skull"},
    Lab.REFERENCE_IDEA: {"reference", "concept", "idea", "composition", "plan"},
    Lab.OPEN_KITCHEN: {"experiment", "explore", "wild", "combine", "discovery"},
}

ACTIVE_PILOT_LABS = {Lab.PERSPECTIVE_ENVIRONMENTS, Lab.LIGHTING_VALUES}


class Coordinator:
    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger

    def route(self, artwork_id: str, request: str, project_id: str = "sketch-lab") -> RouteDecision:
        artwork = self.ledger.get_artwork(project_id, artwork_id)
        if not artwork.primary_lab:
            return RouteDecision("unknown", [], {}, True)
        lowered = request.lower()
        ranked: list[tuple[int, str]] = []
        for lab, words in LAB_KEYWORDS.items():
            if lab == artwork.primary_lab:
                continue
            score = sum(1 for word in words if word in lowered)
            if score:
                ranked.append((score, str(lab)))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        consultants = [lab for _, lab in ranked[:2]]
        reasons = {artwork.primary_lab: "canonical_primary_lab"}
        reasons.update({lab: "request_relevance" for lab in consultants})
        return RouteDecision(artwork.primary_lab, consultants, reasons)

    def parse_requires_confirmation(self, request: str) -> bool:
        lowered = request.lower()
        protected = ("change title", "change primary", "mark complete", "archive", "continue")
        return any(term in lowered for term in protected)

    def classify_intent(self, request: str) -> str:
        """Classify only the intent needed to enforce the read-only boundary.

        This is deliberately narrow. It is not a general natural-language
        router and does not expand the Phase 0-2 architecture.
        """
        lowered = request.lower()
        read_only_phrases = (
            "status only",
            "inventory status",
            "retrieve the current",
            "retrieve current",
            "retrieve the exact",
            "read-only",
            "read only",
        )
        if any(phrase in lowered for phrase in read_only_phrases):
            return "retrieve"
        return "work"

    def run(self, artwork_id: str, request: str, project_id: str = "sketch-lab") -> RunResult:
        artwork = self.ledger.get_artwork(project_id, artwork_id)
        run_id = "RUN-" + hashlib.sha256(f"{project_id}|{artwork_id}|{artwork.version}|{request}".encode()).hexdigest()[:12].upper()
        if self.classify_intent(request) == "retrieve":
            route = RouteDecision(
                artwork.primary_lab,
                [],
                {artwork.primary_lab: "canonical_primary_lab"},
            )
            return RunResult(
                run_id,
                artwork_id,
                artwork.version,
                route,
                [],
                [],
                "",
                False,
            )

        route = self.route(artwork_id, request, project_id)
        findings = []
        for lab in [route.primary_lab, *route.consultants]:
            active = lab in ACTIVE_PILOT_LABS
            findings.append({
                "lab": lab,
                "status": "completed" if active else "deferred_extension",
                "evidence_label": "proposal",
                "statement": self._specialist_statement(lab, request) if active else "Profile registered; runnable specialist deferred beyond Phase 2.",
            })
        approval_required = route.requires_human_confirmation or self.parse_requires_confirmation(request)
        recommendation = self._synthesize(findings)
        self.ledger.remember(project_id, run_id, recommendation, f"artwork:{artwork_id}:v{artwork.version}", "proposal")
        return RunResult(run_id, artwork_id, artwork.version, route, findings, [], recommendation, approval_required)

    def _specialist_statement(self, lab: str, request: str) -> str:
        if lab == Lab.PERSPECTIVE_ENVIRONMENTS:
            return "Protect the spatial hierarchy; correct the largest depth or convergence problem before surface detail."
        if lab == Lab.LIGHTING_VALUES:
            return "Protect the focal light; simplify value groups and verify cast-shadow direction before polishing."
        return f"Bounded review requested: {request}"

    @staticmethod
    def _synthesize(findings: Iterable[dict]) -> str:
        accepted = [f["statement"] for f in findings if f["status"] == "completed"]
        return " ".join(accepted) if accepted else "No runnable specialist was activated; human routing is required."
