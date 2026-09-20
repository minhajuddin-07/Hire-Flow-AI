import uuid
import logging
from typing import List, Optional

from backend.models.requirement import JobRequirement, ExtractedRequirements
from backend.models.job import JobPosting
from backend.llm import (
    get_llm_client,
    sanitize_untrusted_input,
    EXTRACT_JD_PROMPT,
    SYSTEM_SCREENING_INSTRUCTION,
)
from audit import log_entry

logger = logging.getLogger("hireflow.services.jd_parser")


def parse_job_description(
    jd_text: str,
    api_key: Optional[str] = None,
    force_mock: Optional[bool] = None,
) -> JobPosting:
    """
    Step 4: Converts a raw unstructured Job Description into structured requirements.
    Categorizes requirements into:
      - technical_skill
      - experience
      - education
      - domain_knowledge
      - responsibility
      - certification
      - soft_skill
    Separates required (must) and preferred (nice) criteria without fabricating unsupported requirements.
    """
    if not jd_text or not jd_text.strip():
        raise ValueError("Job description text cannot be empty.")

    client = get_llm_client(api_key=api_key, force_mock=force_mock)
    sanitized_jd = sanitize_untrusted_input(jd_text.strip(), tag="job_description_input")
    prompt = EXTRACT_JD_PROMPT.format(jd_data=sanitized_jd)

    extracted: ExtractedRequirements = client.call_structured(
        prompt=prompt,
        schema=ExtractedRequirements,
        system_instruction=SYSTEM_SCREENING_INSTRUCTION,
    )

    requirements = extracted.requirements
    must_count = sum(1 for r in requirements if r.importance == "must")
    nice_count = sum(1 for r in requirements if r.importance == "nice")

    insight_id = f"INSIGHT-JD-{uuid.uuid4().hex[:8].upper()}"
    log_entry(
        insight_id=insight_id,
        step="parse_job_description",
        inputs_used=[{"jd_char_count": len(jd_text), "jd_preview": jd_text[:200]}],
        prompt_version="v1",
        output=[r.model_dump() for r in requirements],
    )

    return JobPosting(
        raw_text=jd_text,
        requirements=requirements,
        must_have_count=must_count,
        nice_to_have_count=nice_count,
    )


def extract_requirements(jd_text: str, api_key: Optional[str] = None) -> List[JobRequirement]:
    """Compatibility helper returning a direct list of JobRequirement items."""
    posting = parse_job_description(jd_text, api_key=api_key)
    return posting.requirements
