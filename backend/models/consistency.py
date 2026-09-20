from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field

InconsistencyCategory = Literal["timeline", "unsupported_claim", "conflicting_dates", "depth_mismatch", "unverified_skill"]
InconsistencySeverity = Literal["low", "medium", "high"]


class ConsistencyFlag(BaseModel):
    """
    Structured flag for unverified claims, conflicting dates, or timeline mismatches.
    Uses neutral, diagnostic language.
    """
    flag_id: str = Field(..., description="Unique flag identifier, e.g. 'FLAG-1'")
    requirement_id: Optional[str] = Field(default=None, description="Related requirement ID if applicable")
    category: InconsistencyCategory = Field(..., description="Category of inconsistency")
    description: str = Field(..., description="Objective description of the mismatch or claim")
    severity: InconsistencySeverity = Field(default="medium", description="Severity level: low, medium, high")
    source_a: str = Field(..., description="First evidence or statement, e.g., resume quote")
    source_b: Optional[str] = Field(default=None, description="Second evidence or statement, e.g., interview answer")
    recommendation: str = Field(
        default="Potential inconsistency detected. Further verification recommended.",
        description="Neutral next-step recommendation",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of detection",
    )
