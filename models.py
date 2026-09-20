from datetime import datetime, timezone
from typing import List, Literal, Optional, Any
from pydantic import BaseModel, Field


class Requirement(BaseModel):
    id: str = Field(..., description="Unique identifier for the requirement, e.g., 'REQ-1'")
    text: str = Field(..., description="Exact requirement description")
    type: Literal["must", "nice"] = Field(..., description="Classification: must-have or nice-to-have")
    weight: float = Field(default=1.0, description="Weight or priority multiplier")


class Evidence(BaseModel):
    source: Literal["resume", "interview"] = Field(..., description="Source of the evidence")
    quote: str = Field(..., description="Verbatim quote from the source text")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp when evidence was extracted"
    )


class HistoryItem(BaseModel):
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of change"
    )
    old_status: Optional[Literal["met", "partial", "unclear", "missing"]] = None
    new_status: Literal["met", "partial", "unclear", "missing"]
    reason: str = Field(..., description="Explanation of why the status changed")


class RequirementRecord(BaseModel):
    requirement_id: str
    status: Literal["met", "partial", "unclear", "missing"] = "missing"
    confidence: Literal["low", "medium", "high"] = "low"
    evidence: List[Evidence] = Field(default_factory=list)
    history: List[HistoryItem] = Field(default_factory=list)


class Question(BaseModel):
    id: str
    requirement_id: str
    text: str


class AuditEntry(BaseModel):
    insight_id: str
    step: str
    inputs_used: List[Any] = Field(default_factory=list)
    prompt_version: str
    output: Any
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ExtractedRequirements(BaseModel):
    requirements: List[Requirement] = Field(
        default_factory=list,
        description="List of extracted candidate requirements"
    )


class ResumeItem(BaseModel):
    category: Literal["skills", "experience", "projects", "qualifications"] = Field(
        ..., description="Category: skills, experience, projects, or qualifications"
    )
    title: str = Field(..., description="Short descriptive title or label of the item")
    quote: str = Field(..., description="Verbatim quote directly from the resume text")


class ExtractedResumeData(BaseModel):
    skills: List[ResumeItem] = Field(default_factory=list)
    experience: List[ResumeItem] = Field(default_factory=list)
    projects: List[ResumeItem] = Field(default_factory=list)
    qualifications: List[ResumeItem] = Field(default_factory=list)


class ValidatedResumeExtraction(BaseModel):
    skills: List[ResumeItem] = Field(default_factory=list)
    experience: List[ResumeItem] = Field(default_factory=list)
    projects: List[ResumeItem] = Field(default_factory=list)
    qualifications: List[ResumeItem] = Field(default_factory=list)
    total_extracted: int = 0
    total_valid: int = 0
    dropped_count: int = 0
    dropped_quotes: List[dict] = Field(default_factory=list)

class ResumeEvaluationResult(BaseModel):
    records: List[RequirementRecord] = Field(
        default_factory=list,
        description="List of requirement records mapping resume evidence to job criteria"
    )
