from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.models.interview import InterviewGap, InterviewQuestion, InterviewAnswer
from backend.models.consistency import ConsistencyFlag
from backend.models.evidence import CandidateEvidence


class RequirementEvaluationSummary(BaseModel):
    """Summary of evaluation for an individual requirement across both resume and interview stages."""
    requirement_id: str
    requirement_text: str
    category: str
    importance: str  # must or nice
    initial_status: str  # CLEAR, PARTIAL, UNCLEAR, MISSING
    final_status: str    # CLEAR, PARTIAL, UNCLEAR, MISSING
    initial_confidence: str
    final_confidence: str
    resume_evidence: List[str] = Field(default_factory=list)
    interview_evidence: List[str] = Field(default_factory=list)
    resolved_in_interview: bool = False
    audit_notes: Optional[str] = None


class CoverageMetrics(BaseModel):
    """Granular coverage statistics."""
    total_requirements: int
    total_covered: int
    coverage_percentage: float
    must_have_total: int
    must_have_covered: int
    must_have_percentage: float
    nice_to_have_total: int
    nice_to_have_covered: int
    nice_to_have_percentage: float


class RecruiterReport(BaseModel):
    """
    Comprehensive, explainable, evidence-based recruiter evaluation report.
    Free of opaque single-number scores. Focuses on factual verified evidence.
    """
    report_id: str = Field(..., description="Unique report identifier, e.g. 'REP-2026-001'")
    candidate_id: str = Field(..., description="Candidate ID")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of generation",
    )
    coverage: CoverageMetrics = Field(..., description="Calculated coverage breakdown")
    requirements_summary: List[RequirementEvaluationSummary] = Field(
        default_factory=list, description="Per-requirement verification status and evidence"
    )
    unresolved_gaps: List[InterviewGap] = Field(
        default_factory=list, description="Remaining uncovered gaps"
    )
    questions_asked: List[InterviewQuestion] = Field(
        default_factory=list, description="Interview questions posed to candidate"
    )
    answers: List[InterviewAnswer] = Field(
        default_factory=list, description="Analyzed answers provided by candidate"
    )
    consistency_flags: List[ConsistencyFlag] = Field(
        default_factory=list, description="Flagged inconsistencies or unverified assertions"
    )
    recruiter_notes: List[str] = Field(
        default_factory=list, description="Objective key recruiter takeaways"
    )
    executive_summary: str = Field(
        ..., description="Evidence-backed executive summary of candidate fit"
    )
