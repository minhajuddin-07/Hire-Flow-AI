from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

EvidenceSource = Literal["resume", "interview"]
EvidenceConfidence = Literal["high", "medium", "low"]
EvidenceStatus = Literal["CLEAR", "PARTIAL", "UNCLEAR", "MISSING"]
LegacyStatus = Literal["met", "partial", "unclear", "missing"]


class CandidateEvidence(BaseModel):
    """
    Evidence item mapped from resume or extracted from interview answers.
    Status is strictly one of CLEAR, PARTIAL, UNCLEAR, MISSING.
    """
    requirement_id: str = Field(..., description="ID of the requirement this evidence addresses")
    evidence: str = Field(..., description="Exact supporting text, quote, or extracted transcript segment")
    source: EvidenceSource = Field(..., description="Source origin: resume or interview")
    confidence: EvidenceConfidence = Field(default="medium", description="Confidence level: high, medium, low")
    status: EvidenceStatus = Field(default="CLEAR", description="Status: CLEAR, PARTIAL, UNCLEAR, MISSING")
    reason: Optional[str] = Field(default=None, description="Explanation or reasoning behind the evaluation")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of evidence capture",
    )

    @property
    def quote(self) -> str:
        """Compatibility property for legacy quote access."""
        return self.evidence


class Evidence(BaseModel):
    """Legacy Evidence model for backward compatibility."""
    source: EvidenceSource = Field(..., description="Source of the evidence")
    quote: str = Field(..., description="Verbatim quote from the source text")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp when evidence was extracted",
    )


class HistoryItem(BaseModel):
    """Tracks state transitions across resume mapping and interview answers."""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of change",
    )
    old_status: Optional[str] = None
    new_status: str
    reason: str = Field(..., description="Explanation of why the status changed")


class RequirementRecord(BaseModel):
    """
    Record storing the current evaluated state, evidence list, and audit history for a requirement.
    """
    requirement_id: str
    status: str = "missing"  # Can be CLEAR/PARTIAL/UNCLEAR/MISSING or lowercase met/partial/unclear/missing
    confidence: EvidenceConfidence = "low"
    evidence: List[Evidence] = Field(default_factory=list)
    history: List[HistoryItem] = Field(default_factory=list)


class ResumeEvaluationResult(BaseModel):
    """Container for requirement records returned by resume evaluation."""
    records: List[RequirementRecord] = Field(
        default_factory=list,
        description="List of requirement records mapping resume evidence to job criteria",
    )
