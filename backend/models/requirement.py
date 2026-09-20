from typing import List, Literal, Optional
from pydantic import BaseModel, Field

RequirementImportance = Literal["must", "nice"]
RequirementCategory = Literal[
    "technical_skill",
    "experience",
    "education",
    "domain_knowledge",
    "responsibility",
    "certification",
    "soft_skill",
]

EvidenceStatus = Literal["CLEAR", "PARTIAL", "UNCLEAR", "MISSING"]


class JobRequirement(BaseModel):
    """
    Structured job requirement model extracted from Job Descriptions.
    Supports both primary fields (requirement, importance) and legacy aliases (text, type).
    """
    id: str = Field(..., description="Unique requirement ID, e.g., 'REQ-1'")
    category: RequirementCategory = Field(
        default="technical_skill",
        description="Category: technical_skill, experience, education, domain_knowledge, responsibility, certification, soft_skill",
    )
    requirement: str = Field(..., description="Concrete requirement text/capability")
    importance: RequirementImportance = Field(
        default="must", description="Classification: must (mandatory) or nice (preferred)"
    )
    evidence_needed: str = Field(
        default="", description="Specific evidence or proof required to verify this requirement"
    )
    keywords: List[str] = Field(
        default_factory=list, description="Associated domain and technical keywords"
    )
    weight: float = Field(default=1.0, description="Priority weight multiplier (e.g. 1.5 - 2.0 for core must-haves)")

    @property
    def text(self) -> str:
        """Alias for backward compatibility."""
        return self.requirement

    @property
    def type(self) -> str:
        """Alias for backward compatibility."""
        return self.importance


class ExtractedRequirements(BaseModel):
    """Container for parsed job requirements."""
    requirements: List[JobRequirement] = Field(
        default_factory=list,
        description="List of extracted candidate requirements",
    )
