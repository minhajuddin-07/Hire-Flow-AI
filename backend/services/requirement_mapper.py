import json
import uuid
import logging
from typing import List, Dict, Optional, Union

from backend.models.requirement import JobRequirement, EvidenceStatus
from backend.models.evidence import (
    CandidateEvidence,
    RequirementRecord,
    Evidence,
    HistoryItem,
    ResumeEvaluationResult,
)
from backend.services.resume_parser import validate_quote
from backend.llm import (
    get_llm_client,
    sanitize_untrusted_input,
    MAP_REQUIREMENTS_PROMPT,
    SYSTEM_SCREENING_INSTRUCTION,
)
from audit import log_entry

logger = logging.getLogger("hireflow.services.requirement_mapper")


def map_status_to_canonical(status_str: str) -> EvidenceStatus:
    """Maps status string to canonical uppercase EvidenceStatus (CLEAR, PARTIAL, UNCLEAR, MISSING)."""
    s = status_str.strip().upper()
    if s in ("MET", "CLEAR"):
        return "CLEAR"
    elif s in ("PARTIAL",):
        return "PARTIAL"
    elif s in ("UNCLEAR",):
        return "UNCLEAR"
    elif s in ("MISSING", "NONE", "UNMET"):
        return "MISSING"
    return "MISSING"


def evaluate_resume_requirements(
    requirements: List[Union[JobRequirement, dict]],
    resume_text: str,
    api_key: Optional[str] = None,
    force_mock: Optional[bool] = None,
) -> List[RequirementRecord]:
    """
    Step 5: Maps resume evidence to each requirement.
    Produces RequirementRecord objects with grounded quotes and calibrated statuses.
    """
    if not requirements:
        raise ValueError("Requirements list cannot be empty.")
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    # Normalize requirements
    req_objs: List[JobRequirement] = []
    for r in requirements:
        if isinstance(r, JobRequirement):
            req_objs.append(r)
        elif isinstance(r, dict):
            req_text = r.get("requirement") or r.get("text", "")
            imp = r.get("importance") or r.get("type", "must")
            req_objs.append(
                JobRequirement(
                    id=r.get("id", "REQ-1"),
                    category=r.get("category", "technical_skill"),
                    requirement=req_text,
                    importance=imp,
                    evidence_needed=r.get("evidence_needed", ""),
                    keywords=r.get("keywords", []),
                    weight=float(r.get("weight", 1.0)),
                )
            )

    client = get_llm_client(api_key=api_key, force_mock=force_mock)
    reqs_json = json.dumps([r.model_dump() for r in req_objs], indent=2)
    sanitized_resume = sanitize_untrusted_input(resume_text.strip(), tag="candidate_resume_input")

    prompt = MAP_REQUIREMENTS_PROMPT.format(
        requirements_json=reqs_json,
        resume_data=sanitized_resume,
    )

    eval_result: ResumeEvaluationResult = client.call_structured(
        prompt=prompt,
        schema=ResumeEvaluationResult,
        system_instruction=SYSTEM_SCREENING_INSTRUCTION,
    )

    record_map = {rec.requirement_id: rec for rec in eval_result.records}
    final_records: List[RequirementRecord] = []

    for req in req_objs:
        rec = record_map.get(req.id)
        if rec is None:
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
            # Enforce Hard Rule 1 quote validation
            valid_evidence: List[Evidence] = []
            for ev in rec.evidence:
                valid_q = validate_quote(ev.quote, resume_text)
                if valid_q is not None:
                    ev.quote = valid_q
                    valid_evidence.append(ev)

            rec.evidence = valid_evidence

            # If evidence was dropped and status was "met" / "CLEAR", adjust to unclear
            if not rec.evidence and rec.status.lower() in ("met", "clear"):
                rec.status = "unclear"
                rec.confidence = "low"

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
    log_entry(
        insight_id=insight_id,
        step="evaluate_resume_requirements",
        inputs_used=[
            {
                "requirement_count": len(req_objs),
                "resume_char_count": len(resume_text),
                "requirement_ids": [r.id for r in req_objs],
            }
        ],
        prompt_version="v1",
        output=[rec.model_dump() for rec in final_records],
    )

    return final_records


def build_candidate_evidence_map(
    requirement_records: List[RequirementRecord],
) -> Dict[str, CandidateEvidence]:
    """Converts legacy RequirementRecord items into typed CandidateEvidence mapping."""
    evidence_map: Dict[str, CandidateEvidence] = {}
    for rec in requirement_records:
        canonical_status = map_status_to_canonical(rec.status)
        quote_text = " | ".join([e.quote for e in rec.evidence]) if rec.evidence else ""
        reason_text = rec.history[-1].reason if rec.history else None

        evidence_map[rec.requirement_id] = CandidateEvidence(
            requirement_id=rec.requirement_id,
            evidence=quote_text,
            source="resume",
            confidence=rec.confidence,
            status=canonical_status,
            reason=reason_text,
        )
    return evidence_map


def update_evidence_with_interview(
    current_evidence_map: Dict[str, CandidateEvidence],
    new_evidence: CandidateEvidence,
) -> Dict[str, CandidateEvidence]:
    """
    Step 8: Live Evidence Update.
    Preserves existing resume evidence while incorporating verified interview evidence.
    Never overwrites evidence blindly.
    """
    updated_map = dict(current_evidence_map)
    existing = updated_map.get(new_evidence.requirement_id)

    if existing is None:
        updated_map[new_evidence.requirement_id] = new_evidence
        return updated_map

    # If interview evidence was obtained, merge evidence sources cleanly
    combined_evidence_str = (
        f"{existing.evidence} | [Interview Verification]: {new_evidence.evidence}".strip(" | ")
        if existing.evidence and new_evidence.evidence
        else (new_evidence.evidence or existing.evidence)
    )

    merged = CandidateEvidence(
        requirement_id=new_evidence.requirement_id,
        evidence=combined_evidence_str,
        source="interview" if new_evidence.source == "interview" else existing.source,
        confidence=new_evidence.confidence,
        status=new_evidence.status,
        reason=f"Updated via interview answer: {new_evidence.reason or 'Evidence verified in interview.'}",
    )
    updated_map[new_evidence.requirement_id] = merged
    return updated_map
