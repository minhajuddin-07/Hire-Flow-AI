import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional

from backend.models.requirement import JobRequirement
from backend.models.candidate import Candidate
from backend.models.evidence import CandidateEvidence
from backend.models.interview import InterviewState, InterviewGap
from backend.models.consistency import ConsistencyFlag
from backend.models.report import (
    RecruiterReport,
    RequirementEvaluationSummary,
    CoverageMetrics,
)
from backend.services.coverage_tracker import calculate_coverage


def generate_recruiter_report(
    candidate_id: str,
    requirements: List[JobRequirement],
    initial_evidence_map: Dict[str, CandidateEvidence],
    final_evidence_map: Dict[str, CandidateEvidence],
    interview_state: Optional[InterviewState] = None,
    consistency_flags: Optional[List[ConsistencyFlag]] = None,
) -> RecruiterReport:
    """
    Step 18: Generates an explainable, evidence-based Recruiter Evaluation Report.
    Avoids opaque single 'hire scores', focusing exclusively on verifiable evidence,
    gap resolutions, and neutral consistency checks.
    """
    coverage = calculate_coverage(requirements, final_evidence_map)
    req_summaries: List[RequirementEvaluationSummary] = []
    unresolved_gaps: List[InterviewGap] = []

    questions_asked = interview_state.questions_asked if interview_state else []
    answers = interview_state.answers if interview_state else []
    flags = consistency_flags or []

    for req in requirements:
        init_ev = initial_evidence_map.get(req.id)
        final_ev = final_evidence_map.get(req.id)

        init_status = init_ev.status if init_ev else "MISSING"
        final_status = final_ev.status if final_ev else "MISSING"

        init_conf = init_ev.confidence if init_ev else "low"
        final_conf = final_ev.confidence if final_ev else "low"

        # Separate resume quotes from interview quotes
        resume_quotes: List[str] = []
        interview_quotes: List[str] = []

        if init_ev and init_ev.evidence:
            resume_quotes.append(init_ev.evidence)

        # Check if interview answer added evidence for this requirement
        relevant_answers = [a for a in answers if a.requirement_id == req.id and a.resolves_gap]
        for a in relevant_answers:
            if a.evidence_found:
                interview_quotes.append(a.evidence_found)

        resolved_in_interview = (
            init_status in ("PARTIAL", "UNCLEAR", "MISSING")
            and final_status == "CLEAR"
        )

        req_summaries.append(
            RequirementEvaluationSummary(
                requirement_id=req.id,
                requirement_text=req.requirement,
                category=req.category,
                importance=req.importance,
                initial_status=init_status,
                final_status=final_status,
                initial_confidence=init_conf,
                final_confidence=final_conf,
                resume_evidence=resume_quotes,
                interview_evidence=interview_quotes,
                resolved_in_interview=resolved_in_interview,
                audit_notes=final_ev.reason if final_ev else None,
            )
        )

        if final_status != "CLEAR":
            unresolved_gaps.append(
                InterviewGap(
                    gap_id=f"GAP-{req.id}",
                    requirement_id=req.id,
                    reason=f"Status remains '{final_status}' after screening.",
                    missing_evidence=req.evidence_needed or req.requirement,
                    priority="HIGH" if req.importance == "must" else "LOW",
                )
            )

    # Compile recruiter notes
    recruiter_notes: List[str] = []
    if coverage.must_have_percentage >= 1.0:
        recruiter_notes.append("100% of mandatory (must-have) technical requirements were successfully verified.")
    elif coverage.must_have_percentage >= 0.75:
        recruiter_notes.append(f"Majority ({coverage.must_have_covered}/{coverage.must_have_total}) of mandatory requirements verified; remaining items require senior review.")
    else:
        recruiter_notes.append(f"Candidate demonstrated gaps in mandatory requirements ({coverage.must_have_covered}/{coverage.must_have_total} met).")

    if flags:
        recruiter_notes.append(f"Identified {len(flags)} consistency diagnostic flag(s) for verification.")

    # Executive summary
    exec_summary = (
        f"Candidate '{candidate_id}' evaluated across {coverage.total_requirements} requirements. "
        f"Overall verified coverage: {int(coverage.coverage_percentage * 100)}% "
        f"(Must-Have: {int(coverage.must_have_percentage * 100)}%, "
        f"Nice-To-Have: {int(coverage.nice_to_have_percentage * 100)}%). "
        f"{'All core requirements satisfied.' if coverage.must_have_percentage >= 1.0 else 'Specific capability gaps remain open.'}"
    )

    report_id = f"REP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    return RecruiterReport(
        report_id=report_id,
        candidate_id=candidate_id,
        coverage=coverage,
        requirements_summary=req_summaries,
        unresolved_gaps=unresolved_gaps,
        questions_asked=questions_asked,
        answers=answers,
        consistency_flags=flags,
        recruiter_notes=recruiter_notes,
        executive_summary=exec_summary,
    )
