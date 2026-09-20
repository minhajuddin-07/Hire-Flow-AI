"""HireFlow Core Data Contract Schema.

Owned by Person 1 (Lead Engineering / Engine).
Defines Pydantic models for roles, requirements, candidates, evidence mappings,
status changes, consistency flags, and auditable insights.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Requirement(BaseModel):
    id: str = Field(..., description="Unique requirement ID (e.g. R1, R2)")
    text: str = Field(..., description="Requirement description")
    category: str = Field(..., description="skill | experience | education | leadership")
    priority: str = Field(default="must_have", description="must_have | nice_to_have")


class Role(BaseModel):
    id: str = Field(..., description="Role ID")
    title: str = Field(..., description="Role title")
    requirements: List[Requirement] = Field(default_factory=list)


class StatusChange(BaseModel):
    from_status: str = Field(..., description="Previous status: Clear | Partial | Unclear | Missing")
    to_status: str = Field(..., description="New status: Clear | Partial | Unclear | Missing")
    reason: str = Field(..., description="Explanation of status transition")
    evidence: str = Field(..., description="Verbatim quote supporting transition")
    source: str = Field(default="interview", description="resume | interview")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"))


class CandidateMapping(BaseModel):
    requirement_id: str
    status: str = Field(..., description="Clear | Partial | Unclear | Missing")
    evidence: Optional[str] = Field(None, description="Verbatim quote from source, verified by code")
    source: str = Field(default="resume", description="resume | interview")
    reasoning: str = Field(default="", description="Why this evidence maps to the requirement")
    needs_validation: bool = Field(default=False, description="True if evidence is partial, unclear, or missing")
    history: List[StatusChange] = Field(default_factory=list)


class ConsistencyFlag(BaseModel):
    type: str = Field(..., description="date_overlap | unbacked_skill | title_inflation")
    description: str = Field(..., description="Neutral factual observation")
    evidence: List[str] = Field(default_factory=list, description="Verbatim quotes or dates involved")


class AuditEntry(BaseModel):
    insight: str = Field(..., description="Human-readable summary of insight/update")
    requirement_id: Optional[str] = None
    inputs_used: str = Field(..., description="Verbatim text or inputs passed to engine")
    model: str = Field(default="gemini-2.5-flash", description="Model or engine rule used")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"))


class CandidateProfile(BaseModel):
    skills: List[Dict[str, str]] = Field(default_factory=list)  # [{"skill": "Python", "quote": "..."}]
    experience: List[Dict[str, str]] = Field(default_factory=list)  # [{"role": "...", "company": "...", "quote": "..."}]
    projects: List[Dict[str, str]] = Field(default_factory=list)  # [{"name": "...", "quote": "..."}]
    education: List[Dict[str, str]] = Field(default_factory=list)  # [{"degree": "...", "quote": "..."}]


class Candidate(BaseModel):
    id: str = Field(..., description="Unique candidate identifier (e.g. c1, c2)")
    name: str = Field(..., description="Full candidate name")
    anon_label: str = Field(..., description="Bias-safe label (e.g. Candidate 1)")
    stage: str = Field(default="screened", description="screened | interviewed")
    summary: str = Field(default="", description="Objective candidate summary")
    profile: CandidateProfile = Field(default_factory=CandidateProfile)
    mappings: List[CandidateMapping] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    interview_questions: List[Dict[str, str]] = Field(default_factory=list)  # [{"requirement_id": "R3", "question": "...", "follow_up": "..."}]
    flags: List[ConsistencyFlag] = Field(default_factory=list)
    interview_log: List[Dict[str, str]] = Field(default_factory=list)
    unanswered_areas: List[str] = Field(default_factory=list)
    audit: List[AuditEntry] = Field(default_factory=list)


class HireFlowPool(BaseModel):
    role: Role
    candidates: List[Candidate] = Field(default_factory=list)
