from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from backend.models.requirement import JobRequirement
from backend.models.job import JobPosting
from backend.models.candidate import Candidate, ValidatedResumeExtraction
from backend.models.evidence import CandidateEvidence, RequirementRecord
from backend.models.interview import (
    InterviewGap,
    InterviewQuestion,
    InterviewAnswer,
    InterviewState,
)
from backend.models.consistency import ConsistencyFlag
from backend.models.report import RecruiterReport, CoverageMetrics
from backend.services.jd_parser import parse_job_description
from backend.services.resume_parser import parse_resume_profile
from backend.services.requirement_mapper import (
    evaluate_resume_requirements,
    build_candidate_evidence_map,
)
from backend.services.gap_detector import detect_gaps
from backend.services.question_generator import generate_interview_question
from backend.services.answer_analyzer import analyze_interview_answer
from backend.services.coverage_tracker import calculate_coverage
from backend.services.consistency_checker import check_consistency
from backend.services.report_generator import generate_recruiter_report
from backend.pipeline.screening_pipeline import screen_candidate, ScreeningResult
from backend.pipeline.interview_pipeline import process_interview_answer, InterviewTurnResult

router = APIRouter(prefix="", tags=["HireFlow AI Engine"])


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------

class AnalyzeJobRequest(BaseModel):
    job_description: str = Field(..., description="Raw Job Description text")
    api_key: Optional[str] = Field(default=None, description="Optional Gemini API key")


class AnalyzeCandidateRequest(BaseModel):
    resume_text: str = Field(..., description="Raw Candidate Resume text")
    api_key: Optional[str] = Field(default=None, description="Optional Gemini API key")


class MapEvidenceRequest(BaseModel):
    requirements: List[JobRequirement] = Field(..., description="Job requirements to evaluate")
    resume_text: str = Field(..., description="Candidate resume text")
    api_key: Optional[str] = Field(default=None, description="Optional Gemini API key")


class DetectGapsRequest(BaseModel):
    requirements: List[JobRequirement] = Field(..., description="List of job requirements")
    evidence_map: Dict[str, CandidateEvidence] = Field(..., description="Current evidence map")


class GenerateQuestionRequest(BaseModel):
    requirement: JobRequirement = Field(..., description="Target job requirement")
    gap: InterviewGap = Field(..., description="Target requirement gap")
    previous_answers: Optional[List[InterviewAnswer]] = Field(
        default=None, description="Prior answers if follow-up question"
    )
    api_key: Optional[str] = Field(default=None, description="Optional Gemini API key")


class AnalyzeAnswerRequest(BaseModel):
    question: InterviewQuestion = Field(..., description="Question asked")
    requirement: JobRequirement = Field(..., description="Target requirement")
    candidate_answer: str = Field(..., description="Candidate's raw answer")
    api_key: Optional[str] = Field(default=None, description="Optional Gemini API key")


class UpdateInterviewRequest(BaseModel):
    interview_state: InterviewState = Field(..., description="Current interview state")
    current_question: InterviewQuestion = Field(..., description="Question answered")
    answer_text: str = Field(..., description="Candidate raw answer text")
    current_evidence_map: Dict[str, CandidateEvidence] = Field(..., description="Current evidence map")
    api_key: Optional[str] = Field(default=None, description="Optional Gemini API key")


class CheckConsistencyRequest(BaseModel):
    resume_text: str = Field(..., description="Resume text")
    interview_answers: Optional[List[InterviewAnswer]] = Field(default=None)


class CalculateCoverageRequest(BaseModel):
    requirements: List[JobRequirement] = Field(...)
    evidence_map: Dict[str, CandidateEvidence] = Field(...)


class GenerateReportRequest(BaseModel):
    candidate_id: str = Field(default="CAND-001")
    requirements: List[JobRequirement] = Field(...)
    initial_evidence_map: Dict[str, CandidateEvidence] = Field(...)
    final_evidence_map: Dict[str, CandidateEvidence] = Field(...)
    interview_state: Optional[InterviewState] = Field(default=None)
    consistency_flags: Optional[List[ConsistencyFlag]] = Field(default=None)


class ScreenCandidateRequest(BaseModel):
    job_description: str = Field(...)
    resume_text: str = Field(...)
    candidate_id: str = Field(default="CAND-001")
    api_key: Optional[str] = Field(default=None)


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "HireFlow AI Backend Engine"}


@router.post("/analyze-job", response_model=JobPosting)
def api_analyze_job(req: AnalyzeJobRequest):
    """Extracts structured requirements from raw job description."""
    try:
        return parse_job_description(req.job_description, api_key=req.api_key)
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/analyze-candidate", response_model=ValidatedResumeExtraction)
def api_analyze_candidate(req: AnalyzeCandidateRequest):
    """Extracts structured, grounded profile from candidate resume."""
    try:
        return parse_resume_profile(req.resume_text, api_key=req.api_key)
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/map-evidence", response_model=List[RequirementRecord])
def api_map_evidence(req: MapEvidenceRequest):
    """Maps resume evidence against requirements."""
    try:
        return evaluate_resume_requirements(
            requirements=req.requirements,
            resume_text=req.resume_text,
            api_key=req.api_key,
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/detect-gaps", response_model=List[InterviewGap])
def api_detect_gaps(req: DetectGapsRequest):
    """Identifies and prioritizes unresolved requirement gaps."""
    try:
        return detect_gaps(req.requirements, req.evidence_map)
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/generate-question", response_model=InterviewQuestion)
def api_generate_question(req: GenerateQuestionRequest):
    """Generates targeted question to resolve a requirement gap."""
    try:
        return generate_interview_question(
            requirement=req.requirement,
            gap=req.gap,
            previous_answers=req.previous_answers,
            api_key=req.api_key,
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/analyze-answer", response_model=InterviewAnswer)
def api_analyze_answer(req: AnalyzeAnswerRequest):
    """Analyzes a candidate interview answer for concrete evidence."""
    try:
        return analyze_interview_answer(
            question=req.question,
            requirement=req.requirement,
            candidate_answer=req.candidate_answer,
            api_key=req.api_key,
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/update-interview", response_model=InterviewTurnResult)
def api_update_interview(req: UpdateInterviewRequest):
    """Processes an adaptive interview turn and advances the session."""
    try:
        return process_interview_answer(
            interview_state=req.interview_state,
            current_question=req.current_question,
            answer_text=req.answer_text,
            current_evidence_map=req.current_evidence_map,
            api_key=req.api_key,
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/check-consistency", response_model=List[ConsistencyFlag])
def api_check_consistency(req: CheckConsistencyRequest):
    """Checks for timeline and claim inconsistencies across statements."""
    try:
        return check_consistency(
            resume_text=req.resume_text,
            interview_answers=req.interview_answers,
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/calculate-coverage", response_model=CoverageMetrics)
def api_calculate_coverage(req: CalculateCoverageRequest):
    """Calculates coverage metrics based on current evidence map."""
    try:
        return calculate_coverage(req.requirements, req.evidence_map)
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/generate-report", response_model=RecruiterReport)
def api_generate_report(req: GenerateReportRequest):
    """Generates comprehensive evidence-based recruiter report."""
    try:
        return generate_recruiter_report(
            candidate_id=req.candidate_id,
            requirements=req.requirements,
            initial_evidence_map=req.initial_evidence_map,
            final_evidence_map=req.final_evidence_map,
            interview_state=req.interview_state,
            consistency_flags=req.consistency_flags,
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/screen-candidate", response_model=ScreeningResult)
def api_screen_candidate(req: ScreenCandidateRequest):
    """End-to-end initial screening pipeline."""
    try:
        return screen_candidate(
            job_description=req.job_description,
            resume=req.resume_text,
            candidate_id=req.candidate_id,
            api_key=req.api_key,
        )
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))
