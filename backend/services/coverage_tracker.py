import logging
from typing import List, Dict, Tuple
from backend.models.requirement import JobRequirement
from backend.models.evidence import CandidateEvidence
from backend.models.report import CoverageMetrics

logger = logging.getLogger("hireflow.services.coverage_tracker")


def calculate_coverage(
    requirements: List[JobRequirement],
    evidence_map: Dict[str, CandidateEvidence],
) -> CoverageMetrics:
    """
    Step 9: Interview Coverage Tracker.
    Computes overall coverage, must-have coverage, and nice-to-have coverage metrics.
    A requirement is considered covered if its status is 'CLEAR' (or 'met').
    """
    if not requirements:
        return CoverageMetrics(
            total_requirements=0,
            total_covered=0,
            coverage_percentage=0.0,
            must_have_total=0,
            must_have_covered=0,
            must_have_percentage=0.0,
            nice_to_have_total=0,
            nice_to_have_covered=0,
            nice_to_have_percentage=0.0,
        )

    total_reqs = len(requirements)
    must_have_reqs = [r for r in requirements if r.importance == "must"]
    nice_to_have_reqs = [r for r in requirements if r.importance == "nice"]

    total_covered = 0
    must_have_covered = 0
    nice_to_have_covered = 0

    for req in requirements:
        ev = evidence_map.get(req.id)
        if ev and ev.status.upper() in ("CLEAR", "MET"):
            total_covered += 1
            if req.importance == "must":
                must_have_covered += 1
            else:
                nice_to_have_covered += 1

    cov_pct = round(total_covered / total_reqs, 3) if total_reqs > 0 else 0.0
    must_pct = (
        round(must_have_covered / len(must_have_reqs), 3)
        if must_have_reqs
        else 1.0
    )
    nice_pct = (
        round(nice_to_have_covered / len(nice_to_have_reqs), 3)
        if nice_to_have_reqs
        else 1.0
    )

    return CoverageMetrics(
        total_requirements=total_reqs,
        total_covered=total_covered,
        coverage_percentage=cov_pct,
        must_have_total=len(must_have_reqs),
        must_have_covered=must_have_covered,
        must_have_percentage=must_pct,
        nice_to_have_total=len(nice_to_have_reqs),
        nice_to_have_covered=nice_to_have_covered,
        nice_to_have_percentage=nice_pct,
    )


def partition_requirements_by_coverage(
    requirements: List[JobRequirement],
    evidence_map: Dict[str, CandidateEvidence],
) -> Tuple[List[JobRequirement], List[JobRequirement]]:
    """Partitions requirements into covered list and unresolved list."""
    covered: List[JobRequirement] = []
    unresolved: List[JobRequirement] = []

    for req in requirements:
        ev = evidence_map.get(req.id)
        if ev and ev.status.upper() in ("CLEAR", "MET"):
            covered.append(req)
        else:
            unresolved.append(req)

    return covered, unresolved
