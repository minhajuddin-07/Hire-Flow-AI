from datetime import datetime, timezone
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.models.requirement import JobRequirement
from backend.models.evidence import CandidateEvidence

PriorityLevel = Literal["HIGH", "MEDIUM", "LOW"]
ConfidenceLevel = Literal["high", "medium", "low"]


class InterviewGap(BaseModel):
    """Identified requirement gap requiring interview verification."""
    gap_id: str = Field(..., description="Unique gap identifier, e.g. 'GAP-1'")
    requirement_id: str = Field(..., description="Target requirement identifier, e.g. 'REQ-1'")
    reason: str = Field(..., description="Diagnostic explanation of why the gap exists")
    missing_evidence: str = Field(..., description="Exact capability or detail missing from the resume")
    priority: PriorityLevel = Field(default="HIGH", description="Priority level: HIGH, MEDIUM, LOW")


class InterviewQuestion(BaseModel):
    """Targeted interview question crafted to resolve a specific gap."""
    question_id: str = Field(..., description="Unique question identifier, e.g. 'Q-1'")
    requirement_id: str = Field(..., description="Target requirement ID, e.g. 'REQ-1'")
    purpose: str = Field(..., description="Objective of this question in evaluating the candidate")
    question: str = Field(..., description="Targeted question text for the candidate")
    expected_evidence: str = Field(..., description="Key technical evidence or details expected in a strong answer")
    priority: PriorityLevel = Field(default="HIGH", description="Priority level: HIGH, MEDIUM, LOW")
    is_follow_up: bool = Field(default=False, description="Whether this is a follow-up to a previous answer")
    parent_question_id: Optional[str] = Field(default=None, description="Parent question ID if follow-up")

    @property
    def id(self) -> str:
        """Compatibility property."""
        return self.question_id

    @property
    def text(self) -> str:
        """Compatibility property."""
        return self.question


class InterviewAnswer(BaseModel):
    """Structured analysis of a candidate's interview answer."""
    question_id: str = Field(..., description="Referenced question identifier")
    requirement_id: str = Field(..., description="Target requirement identifier")
    answer: str = Field(..., description="Candidate's raw verbatim answer text")
    evidence_found: Optional[str] = Field(
        default=None, description="Extracted supporting evidence quote/summary from the answer"
    )
    confidence: ConfidenceLevel = Field(default="medium", description="Confidence in extracted evidence")
    resolves_gap: bool = Field(default=False, description="Whether the answer sufficiently resolves the gap")
    follow_up_needed: bool = Field(default=False, description="Whether follow-up clarification is needed")
    follow_up_focus: Optional[str] = Field(
        default=None, description="Suggested angle or prompt if follow-up is needed"
    )
    reasoning: str = Field(
        default="", description="Objective justification for the evaluation of this answer"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of answer analysis",
    )


class InterviewState(BaseModel):
    """
    Live state of the adaptive interview session.
    Tracks covered vs unresolved requirements, transcript history, dynamic evidence, and coverage metrics.
    """
    session_id: str = Field(default="default-session", description="Unique session ID")
    candidate_id: str = Field(default="CAND-001", description="Candidate ID")
    job_requirements: List[JobRequirement] = Field(default_factory=list, description="All job requirements")
    covered_requirements: List[str] = Field(
        default_factory=list, description="IDs of requirements evaluated as CLEAR/met"
    )
    unresolved_requirements: List[str] = Field(
        default_factory=list, description="IDs of requirements with remaining gaps (PARTIAL/UNCLEAR/MISSING)"
    )
    gaps: List[InterviewGap] = Field(default_factory=list, description="Current list of active gaps")
    questions_asked: List[InterviewQuestion] = Field(default_factory=list, description="All questions asked")
    answers: List[InterviewAnswer] = Field(default_factory=list, description="All analyzed answers")
    evidence_updates: List[CandidateEvidence] = Field(
        default_factory=list, description="All evidence collected (resume + interview)"
    )
    coverage_percentage: float = Field(
        default=0.0, description="Overall coverage ratio (0.0 to 1.0 or 0 to 100)"
    )
    must_have_coverage_percentage: float = Field(
        default=0.0, description="Coverage ratio specifically for must-have requirements"
    )
    current_turn: int = Field(default=0, description="Number of interview turns completed")
    max_turns: int = Field(default=5, description="Maximum allowed interview turns")
    is_completed: bool = Field(default=False, description="Whether the interview session has completed")


class Question(BaseModel):
    """Legacy question model for backward compatibility."""
    id: str
    requirement_id: str
    text: str
