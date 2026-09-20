import logging
from typing import Optional, List

from backend.models.requirement import JobRequirement
from backend.models.interview import InterviewGap, InterviewQuestion, InterviewAnswer
from backend.llm import (
    get_llm_client,
    GENERATE_QUESTION_PROMPT,
    SYSTEM_SCREENING_INSTRUCTION,
)

logger = logging.getLogger("hireflow.services.question_generator")


def generate_interview_question(
    requirement: JobRequirement,
    gap: InterviewGap,
    previous_answers: Optional[List[InterviewAnswer]] = None,
    api_key: Optional[str] = None,
    force_mock: Optional[bool] = None,
) -> InterviewQuestion:
    """
    Step 7: Generates a targeted, probing interview question designed to resolve a specific gap.
    If previous answers exist for this requirement and were marked as needing follow-up, generates a follow-up question.
    """
    client = get_llm_client(api_key=api_key, force_mock=force_mock)

    is_follow_up = False
    parent_q_id = None
    history_context = "None"

    if previous_answers:
        related_answers = [a for a in previous_answers if a.requirement_id == requirement.id]
        if related_answers:
            is_follow_up = True
            parent_q_id = related_answers[-1].question_id
            history_context = (
                f"Previous Answer: '{related_answers[-1].answer}' | "
                f"Previous Analysis: '{related_answers[-1].reasoning}' | "
                f"Follow-up Focus: '{related_answers[-1].follow_up_focus}'"
            )

    prompt = GENERATE_QUESTION_PROMPT.format(
        requirement_id=requirement.id,
        requirement_text=requirement.requirement,
        importance=requirement.importance,
        missing_evidence=gap.missing_evidence,
        history_context=history_context,
    )

    question: InterviewQuestion = client.call_structured(
        prompt=prompt,
        schema=InterviewQuestion,
        system_instruction=SYSTEM_SCREENING_INSTRUCTION,
    )

    # Ensure metadata fields are consistently populated
    question.requirement_id = requirement.id
    question.priority = gap.priority
    question.is_follow_up = is_follow_up
    question.parent_question_id = parent_q_id

    return question
