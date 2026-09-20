import logging
from typing import Optional

from backend.models.requirement import JobRequirement
from backend.models.interview import InterviewQuestion, InterviewAnswer
from backend.llm import (
    get_llm_client,
    sanitize_untrusted_input,
    ANALYZE_ANSWER_PROMPT,
    SYSTEM_SCREENING_INSTRUCTION,
)

logger = logging.getLogger("hireflow.services.answer_analyzer")


def analyze_interview_answer(
    question: InterviewQuestion,
    requirement: JobRequirement,
    candidate_answer: str,
    api_key: Optional[str] = None,
    force_mock: Optional[bool] = None,
) -> InterviewAnswer:
    """
    Step 10: Analyzes candidate interview answers strictly against technical requirement criteria.
    Extracts concrete evidence quotes, determines gap resolution, and identifies follow-up need.
    Treats candidate answer text strictly as untrusted input.
    """
    if not candidate_answer or not candidate_answer.strip():
        return InterviewAnswer(
            question_id=question.question_id,
            requirement_id=requirement.id,
            answer="",
            evidence_found=None,
            confidence="low",
            resolves_gap=False,
            follow_up_needed=True,
            follow_up_focus="Candidate provided empty response.",
            reasoning="No answer provided by candidate.",
        )

    client = get_llm_client(api_key=api_key, force_mock=force_mock)
    sanitized_answer = sanitize_untrusted_input(candidate_answer.strip(), tag="candidate_answer_input")

    prompt = ANALYZE_ANSWER_PROMPT.format(
        requirement_id=requirement.id,
        requirement_text=requirement.requirement,
        expected_evidence=question.expected_evidence,
        question_text=question.question,
        answer_data=sanitized_answer,
    )

    analyzed: InterviewAnswer = client.call_structured(
        prompt=prompt,
        schema=InterviewAnswer,
        system_instruction=SYSTEM_SCREENING_INSTRUCTION,
    )

    analyzed.question_id = question.question_id
    analyzed.requirement_id = requirement.id
    analyzed.answer = candidate_answer.strip()

    return analyzed
