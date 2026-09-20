import uuid
import re
import json
from typing import List, Optional, Union
from models import (
    Requirement,
    ExtractedRequirements,
    ResumeItem,
    ExtractedResumeData,
    ValidatedResumeExtraction,
    RequirementRecord,
    Evidence,
    HistoryItem,
    ResumeEvaluationResult,
)
from llm import (
    call_json,
    EXTRACT_REQUIREMENTS_PROMPT_V1,
    EXTRACT_RESUME_PROMPT_V1,
    MAP_RESUME_EVALUATION_PROMPT_V1,
    PROMPT_VERSION,
)
from audit import log_entry


def extract_requirements(jd_text: str, api_key: str = None) -> List[Requirement]:
    """
    Extracts structured requirements from the raw Job Description text.
    Enforces must/nice classification and weights.
    Logs every extraction to the audit trail.
    """
    if not jd_text or not jd_text.strip():
        raise ValueError("Job description text cannot be empty.")

    prompt = EXTRACT_REQUIREMENTS_PROMPT_V1.format(jd_text=jd_text.strip())

    extracted: ExtractedRequirements = call_json(
        prompt=prompt,
        schema=ExtractedRequirements,
        prompt_version=PROMPT_VERSION,
        api_key=api_key,
    )

    insight_id = f"INSIGHT-JD-{uuid.uuid4().hex[:8].upper()}"

    # Log to audit trail
    log_entry(
        insight_id=insight_id,
        step="extract_requirements",
        inputs_used=[{"jd_char_count": len(jd_text), "jd_preview": jd_text[:300]}],
        prompt_version=PROMPT_VERSION,
        output=[req.model_dump() for req in extracted.requirements],
    )

    return extracted.requirements


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

    # 1. Exact verbatim substring match
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

    return None


def extract_resume_profile(resume_text: str, api_key: str = None) -> ValidatedResumeExtraction:
    """
    Extracts structured skills, experience, projects, and qualifications from the candidate resume.
    Applies Hard Rule 1 Quote Validation to ensure 100% verbatim grounding in resume text.
    Drops any hallucinated/unmatched quotes and records dropped quote count.
    Logs extraction and validation to the audit trail.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    prompt = EXTRACT_RESUME_PROMPT_V1.format(resume_text=resume_text.strip())

    extracted: ExtractedResumeData = call_json(
        prompt=prompt,
        schema=ExtractedResumeData,
        prompt_version=PROMPT_VERSION,
        api_key=api_key,
    )

    # Apply Hard Rule 1 Quote Validator across all categories
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
            valid_quote = validate_quote(item.quote, resume_text)
            if valid_quote is not None:
                # Update with exact grounded slice from resume text
                item.quote = valid_quote
                validated_items.append(item)
            else:
                # Hard Rule 1 violation: drop quote
                validated.dropped_count += 1
                validated.dropped_quotes.append({
                    "category": cat_name,
                    "title": item.title,
                    "quote": item.quote,
                    "reason": "Verbatim quote not found in resume text (Hard Rule 1 violation)",
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

    # Log to audit trail
    log_entry(
        insight_id=insight_id,
        step="extract_resume",
        inputs_used=[{"resume_char_count": len(resume_text), "resume_preview": resume_text[:300]}],
        prompt_version=PROMPT_VERSION,
        output=validated.model_dump(),
    )

    return validated


def evaluate_resume_requirements(
    requirements: List[Union[Requirement, dict]],
    resume_text: str,
    api_key: Optional[str] = None,
) -> List[RequirementRecord]:
    """
    Step 3: For each requirement, maps resume evidence to it and sets status
    (met/partial/unclear/missing), confidence (low/medium/high), and supporting quotes,
    creating one RequirementRecord per requirement.
    Enforces Hard Rule 1: All quotes must be verbatim substrings from the resume text.
    Logs evaluation to audit trail.
    """
    if not requirements:
        raise ValueError("Requirements list cannot be empty.")
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    # Standardize requirements objects
    req_objs: List[Requirement] = [
        r if isinstance(r, Requirement) else Requirement(**r) for r in requirements
    ]

    reqs_json = json.dumps([r.model_dump() for r in req_objs], indent=2)
    prompt = MAP_RESUME_EVALUATION_PROMPT_V1.format(
        requirements_json=reqs_json,
        resume_text=resume_text.strip(),
    )

    eval_result: ResumeEvaluationResult = call_json(
        prompt=prompt,
        schema=ResumeEvaluationResult,
        prompt_version=PROMPT_VERSION,
        api_key=api_key,
    )

    # Build lookup of returned records
    record_map = {rec.requirement_id: rec for rec in eval_result.records}
    final_records: List[RequirementRecord] = []

    for req in req_objs:
        rec = record_map.get(req.id)
        if rec is None:
            # Create a default missing record if not returned
            rec = RequirementRecord(
                requirement_id=req.id,
                status="missing",
                confidence="low",
                evidence=[],
                history=[
                    HistoryItem(
                        old_status=None,
                        new_status="missing",
                        reason="No evidence found in candidate resume.",
                    )
                ],
            )
        else:
            # Enforce Hard Rule 1 on all supporting quotes
            validated_evidence: List[Evidence] = []
            for ev in rec.evidence:
                valid_q = validate_quote(ev.quote, resume_text)
                if valid_q is not None:
                    ev.quote = valid_q
                    validated_evidence.append(ev)

            rec.evidence = validated_evidence

            # If evidence was dropped and status was "met", adjust status
            if not rec.evidence and rec.status == "met":
                rec.status = "unclear"
                rec.confidence = "low"

            # Ensure initial history entry exists
            if not rec.history:
                rec.history.append(
                    HistoryItem(
                        old_status=None,
                        new_status=rec.status,
                        reason=f"Initial mapping evaluated status as '{rec.status}'.",
                    )
                )

        final_records.append(rec)

    insight_id = f"INSIGHT-EVAL-{uuid.uuid4().hex[:8].upper()}"

    # Log to audit trail
    log_entry(
        insight_id=insight_id,
        step="map_resume_requirements",
        inputs_used=[
            {
                "requirement_count": len(req_objs),
                "resume_char_count": len(resume_text),
                "requirement_ids": [r.id for r in req_objs],
            }
        ],
        prompt_version=PROMPT_VERSION,
        output=[rec.model_dump() for rec in final_records],
    )

    return final_records


