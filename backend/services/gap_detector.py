import logging
from typing import List, Dict, Optional

from backend.models.requirement import JobRequirement
from backend.models.evidence import CandidateEvidence
from backend.models.interview import InterviewGap, PriorityLevel

logger = logging.getLogger("hireflow.services.gap_detector")


def detect_gaps(
    requirements: List[JobRequirement],
    evidence_map: Dict[str, CandidateEvidence],
) -> List[InterviewGap]:
    """
    Step 6: Gap Detection.
    Identifies all unresolved requirements (PARTIAL, UNCLEAR, MISSING) and generates
    prioritized InterviewGap objects.
    Prioritizes must-have requirements and higher weight criteria first.
    """
    gaps: List[InterviewGap] = []
    gap_counter = 1

    for req in requirements:
        ev = evidence_map.get(req.id)
        status = ev.status if ev else "MISSING"

        if status in ("PARTIAL", "UNCLEAR", "MISSING"):
            # Determine gap priority based on requirement importance and weight
            priority: PriorityLevel = "HIGH"
            if req.importance == "must":
                priority = "HIGH"
            elif req.weight >= 1.5:
                priority = "HIGH"
            elif req.importance == "nice" and req.weight >= 1.0:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            reason_desc = (
                ev.reason
                if ev and ev.reason
                else f"Requirement '{req.requirement[:60]}' has status '{status}' in resume evaluation."
            )

            missing_desc = (
                req.evidence_needed
                or f"Concrete production evidence and verifiable depth for: {req.requirement}"
            )

            gaps.append(
                InterviewGap(
                    gap_id=f"GAP-{gap_counter}",
                    requirement_id=req.id,
                    reason=reason_desc,
                    missing_evidence=missing_desc,
                    priority=priority,
                )
            )
            gap_counter += 1

    # Sort gaps: HIGH priority first, then by matching requirement weight descending
    req_weight_map = {r.id: r.weight for r in requirements}
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

    gaps.sort(
        key=lambda g: (
            priority_order.get(g.priority, 1),
            -req_weight_map.get(g.requirement_id, 1.0),
        )
    )

    return gaps


def get_next_unresolved_gap(
    gaps: List[InterviewGap],
    already_asked_requirement_ids: List[str],
) -> Optional[InterviewGap]:
    """Returns the highest priority gap that has not yet been addressed in the interview."""
    for gap in gaps:
        if gap.requirement_id not in already_asked_requirement_ids:
            return gap
    return None
