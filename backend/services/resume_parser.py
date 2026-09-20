import re
import uuid
import logging
from typing import Optional, List

from backend.models.candidate import (
    ResumeItem,
    ExtractedResumeData,
    ValidatedResumeExtraction,
)
from backend.llm import (
    get_llm_client,
    sanitize_untrusted_input,
    EXTRACT_RESUME_PROMPT,
    SYSTEM_SCREENING_INSTRUCTION,
)
from audit import log_entry

logger = logging.getLogger("hireflow.services.resume_parser")


def validate_quote(quote: str, source_text: str) -> Optional[str]:
    """
    Hard Rule 1: Verbatim Quote Validator.
    Checks whether a quote exists verbatim in the source text.
    Returns the exact verified substring from source_text, or None if ungrounded/hallucinated.
    """
    if not quote or not source_text:
        return None

    clean_quote = quote.strip().strip('\'"`“”')
    if not clean_quote:
        return None

    # 1. Exact verbatim match
    if clean_quote in source_text:
        return clean_quote

    # 2. Whitespace-normalized slice match
    norm_quote = re.sub(r"\s+", " ", clean_quote)
    norm_source = re.sub(r"\s+", " ", source_text)
    if norm_quote.lower() in norm_source.lower():
        escaped = re.escape(norm_quote).replace(r"\ ", r"\s+")
        match = re.search(escaped, source_text, re.IGNORECASE)
        if match:
            return match.group(0)

    # 3. Line-by-line containment check for multiline items
    for line in source_text.splitlines():
        line_clean = line.strip()
        if clean_quote.lower() in line_clean.lower() and len(line_clean) >= len(clean_quote) * 0.8:
            return line_clean

    return None


def parse_resume_profile(
    resume_text: str,
    api_key: Optional[str] = None,
    force_mock: Optional[bool] = None,
) -> ValidatedResumeExtraction:
    """
    Step 5: Extracts structured skills, experience, projects, and qualifications from the candidate resume.
    Applies Hard Rule 1 Quote Validation to ensure 100% verbatim grounding in resume text.
    Drops any hallucinated quotes and logs to audit trail.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    client = get_llm_client(api_key=api_key, force_mock=force_mock)
    sanitized_resume = sanitize_untrusted_input(resume_text.strip(), tag="candidate_resume_input")
    prompt = EXTRACT_RESUME_PROMPT.format(resume_data=sanitized_resume)

    extracted: ExtractedResumeData = client.call_structured(
        prompt=prompt,
        schema=ExtractedResumeData,
        system_instruction=SYSTEM_SCREENING_INSTRUCTION,
    )

    validated = ValidatedResumeExtraction()
    total_extracted = 0

    category_map = {
        "skills": extracted.skills,
        "experience": extracted.experience,
        "projects": extracted.projects,
        "qualifications": extracted.qualifications,
    }

    for cat_name, item_list in category_map.items():
        validated_items = []
        for item in item_list:
            total_extracted += 1
            valid_q = validate_quote(item.quote, resume_text)
            if valid_q is not None:
                item.quote = valid_q
                validated_items.append(item)
            else:
                validated.dropped_count += 1
                validated.dropped_quotes.append({
                    "category": cat_name,
                    "title": item.title,
                    "quote": item.quote,
                    "reason": "Quote not found verbatim in resume text (Hard Rule 1 violation)",
                })

        if cat_name == "skills":
            validated.skills = validated_items
        elif cat_name == "experience":
            validated.experience = validated_items
        elif cat_name == "projects":
            validated.projects = validated_items
        elif cat_name == "qualifications":
            validated.qualifications = validated_items

    validated.total_extracted = total_extracted
    validated.total_valid = (
        len(validated.skills)
        + len(validated.experience)
        + len(validated.projects)
        + len(validated.qualifications)
    )

    insight_id = f"INSIGHT-RESUME-{uuid.uuid4().hex[:8].upper()}"
    log_entry(
        insight_id=insight_id,
        step="parse_resume_profile",
        inputs_used=[{"resume_char_count": len(resume_text), "resume_preview": resume_text[:200]}],
        prompt_version="v1",
        output=validated.model_dump(),
    )

    return validated


def extract_resume_profile(resume_text: str, api_key: Optional[str] = None) -> ValidatedResumeExtraction:
    """Compatibility alias."""
    return parse_resume_profile(resume_text, api_key=api_key)
