from typing import List, Optional
from pydantic import BaseModel, Field
from backend.models.requirement import JobRequirement


class JobPosting(BaseModel):
    """Represents a job posting and its extracted criteria."""
    title: Optional[str] = Field(default=None, description="Job title if identified")
    raw_text: str = Field(..., description="Original unstructured job description text")
    requirements: List[JobRequirement] = Field(
        default_factory=list, description="Extracted structured requirements"
    )
    must_have_count: int = Field(default=0, description="Count of mandatory requirements")
    nice_to_have_count: int = Field(default=0, description="Count of preferred requirements")
