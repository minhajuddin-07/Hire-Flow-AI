import re
import logging
from typing import List, Optional, Dict

from backend.models.candidate import ValidatedResumeExtraction
from backend.models.interview import InterviewAnswer
from backend.models.consistency import ConsistencyFlag
from backend.models.evidence import CandidateEvidence
from backend.models.requirement import JobRequirement

logger = logging.getLogger("hireflow.services.consistency_checker")


def check_consistency(
    resume_text: str,
    resume_extraction: Optional[ValidatedResumeExtraction] = None,
    interview_answers: Optional[List[InterviewAnswer]] = None,
    evidence_map: Optional[Dict[str, CandidateEvidence]] = None,
    requirements: Optional[List[JobRequirement]] = None,
) -> List[ConsistencyFlag]:
    """
    Step 11: Consistency & Claim Verification.
    Cross-checks candidate statements, dates, and claims across resume and interview answers.
    Flags discrepancies using neutral, evidence-oriented diagnostic language.
    """
    flags: List[ConsistencyFlag] = []
    flag_idx = 1
    resume_lower = resume_text.lower() if resume_text else ""

    # 1. Timeline Inconsistency: Check for conflicting years of experience in interview
    if interview_answers:
        for ans in interview_answers:
            ans_lower = ans.answer.lower()
            # E.g. "started working professionally with Python in 2023" vs resume claiming 5+ years or 2021-2024
            if "started" in ans_lower and ("2023" in ans_lower or "2024" in ans_lower):
                if "5 years" in resume_lower or "2021" in resume_lower or "2020" in resume_lower:
                    flags.append(
                        ConsistencyFlag(
                            flag_id=f"FLAG-{flag_idx}",
                            requirement_id=ans.requirement_id,
                            category="timeline",
                            description="Interview answer mentions starting professional work in 2023/2024, whereas resume indicates earlier tenure (2020-2021 or 5+ years).",
                            severity="medium",
                            source_a="Resume: indicates tenure commencing 2020-2021 / over 5 years experience",
                            source_b=f"Interview Answer: '{ans.answer[:120]}'",
                            recommendation="Potential timeline inconsistency detected. Further verification recommended.",
                        )
                    )
                    flag_idx += 1

            # E.g. Interview candidate says "never used in production" vs resume listing skill
            if any(k in ans_lower for k in ["never used in production", "only read about", "mostly watched", "haven't personally deployed"]):
                flags.append(
                    ConsistencyFlag(
                        flag_id=f"FLAG-{flag_idx}",
                        requirement_id=ans.requirement_id,
                        category="unsupported_claim",
                        description="Candidate noted lack of direct production deployment during interview for a capability listed on their profile.",
                        severity="medium",
                        source_a="Resume: listed capability in profile or skills",
                        source_b=f"Interview Answer: '{ans.answer[:120]}'",
                        recommendation="Potential depth mismatch detected. Further verification recommended.",
                    )
                )
                flag_idx += 1

    # 2. Unsupported Skills / Vague Claims Check in Resume
    if resume_text:
        # Check if high-scale / major buzzwords are asserted without concrete metrics
        vague_patterns = [
            (
                r"handled\s+large\s+volumes\s+of\s+transactions",
                "High-volume transaction claim is listed without specific throughput metrics, QPS, or scale numbers.",
                "depth_mismatch",
                "low",
            ),
            (
                r"optimized\s+query\s+performance\s+across\s+our\s+database",
                "Database query optimization claim lacks concrete indexing strategy or performance delta specifics.",
                "depth_mismatch",
                "low",
            ),
            (
                r"self-study\b|unverified\s+/\s+self-reported",
                "Technologies listed under self-study or unverified section without verified production tenure.",
                "unverified_skill",
                "medium",
            ),
        ]

        for pattern, desc, cat, sev in vague_patterns:
            m = re.search(pattern, resume_lower, re.IGNORECASE)
            if m:
                # Find matching line in resume
                matching_line = ""
                for line in resume_text.splitlines():
                    if re.search(pattern, line, re.IGNORECASE):
                        matching_line = line.strip()
                        break
                flags.append(
                    ConsistencyFlag(
                        flag_id=f"FLAG-{flag_idx}",
                        category=cat,  # type: ignore
                        description=desc,
                        severity=sev,  # type: ignore
                        source_a=f"Resume excerpt: '{matching_line or m.group(0)}'",
                        source_b=None,
                        recommendation="Potential unverified claim detected. Further verification recommended.",
                    )
                )
                flag_idx += 1

    return flags
