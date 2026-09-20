import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from backend.models.requirement import JobRequirement
from backend.models.candidate import Candidate, ValidatedResumeExtraction
from backend.models.evidence import CandidateEvidence, RequirementRecord
from backend.models.interview import InterviewGap, InterviewQuestion
from backend.models.consistency import ConsistencyFlag
from backend.models.report import CoverageMetrics
from backend.services.jd_parser import parse_job_description
from backend.services.resume_parser import parse_resume_profile
from backend.services.requirement_mapper import (
    evaluate_resume_requirements,
    build_candidate_evidence_map,
)
from backend.services.gap_detector import detect_gaps
from backend.services.consistency_checker import check_consistency
from backend.services.coverage_tracker import calculate_coverage
from backend.services.question_generator import generate_interview_question

logger = logging.getLogger("hireflow.pipeline.screening")


class ScreeningResult(BaseModel):
    """Encapsulates all outputs from the initial candidate screening pipeline."""
    candidate: Candidate
    job_requirements: List[JobRequirement]
    requirement_records: List[RequirementRecord]
    evidence_map: Dict[str, CandidateEvidence]
    gaps: List[InterviewGap]
    consistency_flags: List[ConsistencyFlag]
    initial_coverage: CoverageMetrics
    suggested_initial_questions: List[InterviewQuestion] = Field(default_factory=list)


def screen_candidate(
    job_description: str,
    resume: str,
    candidate_id: str = "CAND-001",
    api_key: Optional[str] = None,
    force_mock: Optional[bool] = None,
) -> ScreeningResult:
    """
    Step 17: End-to-End Candidate Screening Pipeline.
    Orchestrates:
      JD Extraction -> Resume Analysis -> Evidence Mapping -> Gap Detection -> Consistency Checking -> Interview Plan
    """
    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty.")
    if not resume or not resume.strip():
        raise ValueError("Resume text cannot be empty.")

    # 1. Extract requirements from JD
    posting = parse_job_description(job_description, api_key=api_key, force_mock=force_mock)
    requirements = posting.requirements

    # 2. Extract structured profile from resume with Hard Rule 1 quote validation
    resume_extraction = parse_resume_profile(resume, api_key=api_key, force_mock=force_mock)

    # 3. Map resume evidence to each requirement
    records = evaluate_resume_requirements(
        requirements=requirements,
        resume_text=resume,
        api_key=api_key,
        force_mock=force_mock,
    )
    evidence_map = build_candidate_evidence_map(records)

    # 4. Detect requirement gaps
    gaps = detect_gaps(requirements, evidence_map)

    # 5. Check consistency & claim validation
    flags = check_consistency(
        resume_text=resume,
        resume_extraction=resume_extraction,
        evidence_map=evidence_map,
        requirements=requirements,
    )

    # 6. Calculate initial coverage
    coverage = calculate_coverage(requirements, evidence_map)

    # 7. Generate initial questions for top gaps
    initial_questions: List[InterviewQuestion] = []
    for gap in gaps[:3]:
        req = next((r for r in requirements if r.id == gap.requirement_id), None)
        if req:
            q = generate_interview_question(
                requirement=req,
                gap=gap,
                api_key=api_key,
                force_mock=force_mock,
            )
            initial_questions.append(q)

    # Assemble complete Candidate model
    candidate = Candidate(
        candidate_id=candidate_id,
        resume_text=resume,
        extracted_information=resume_extraction,
        evidence_map=evidence_map,
        gaps=gaps,
        consistency_flags=flags,
    )

    return ScreeningResult(
        candidate=candidate,
        job_requirements=requirements,
        requirement_records=records,
        evidence_map=evidence_map,
        gaps=gaps,
        consistency_flags=flags,
        initial_coverage=coverage,
        suggested_initial_questions=initial_questions,
    )
