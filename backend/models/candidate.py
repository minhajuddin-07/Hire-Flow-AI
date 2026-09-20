from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from backend.models.evidence import CandidateEvidence
from backend.models.interview import InterviewGap
from backend.models.consistency import ConsistencyFlag

ResumeCategory = Literal["skills", "experience", "projects", "qualifications"]


class ResumeItem(BaseModel):
    """Extracted item from a candidate resume with verbatim quote grounding."""
    category: ResumeCategory = Field(
        ..., description="Category: skills, experience, projects, or qualifications"
    )
    title: str = Field(..., description="Short descriptive title or label of the item")
    quote: str = Field(..., description="Verbatim quote directly from the resume text")


class ExtractedResumeData(BaseModel):
    """Raw extracted sections from resume."""
    skills: List[ResumeItem] = Field(default_factory=list)
    experience: List[ResumeItem] = Field(default_factory=list)
    projects: List[ResumeItem] = Field(default_factory=list)
    qualifications: List[ResumeItem] = Field(default_factory=list)


class ValidatedResumeExtraction(BaseModel):
    """Validated structured resume data where all quotes are verified against source text."""
    skills: List[ResumeItem] = Field(default_factory=list)
    experience: List[ResumeItem] = Field(default_factory=list)
    projects: List[ResumeItem] = Field(default_factory=list)
    qualifications: List[ResumeItem] = Field(default_factory=list)
    total_extracted: int = 0
    total_valid: int = 0
    dropped_count: int = 0
    dropped_quotes: List[dict] = Field(default_factory=list)


class Candidate(BaseModel):
    """
    Complete candidate profile spanning resume extraction, evidence mapping,
    identified gaps, and consistency diagnostics.
    """
    candidate_id: str = Field(default="CAND-001", description="Unique candidate ID")
    name: Optional[str] = Field(default=None, description="Candidate name if extracted")
    resume_text: str = Field(..., description="Raw resume text")
    extracted_information: ValidatedResumeExtraction = Field(
        default_factory=ValidatedResumeExtraction,
        description="Validated structured resume entities",
    )
    evidence_map: Dict[str, CandidateEvidence] = Field(
        default_factory=dict,
        description="Mapping from requirement_id to CandidateEvidence",
    )
    gaps: List[InterviewGap] = Field(
        default_factory=list,
        description="Identified requirement gaps for this candidate",
    )
    consistency_flags: List[ConsistencyFlag] = Field(
        default_factory=list,
        description="Flags for unverified or conflicting claims",
    )
