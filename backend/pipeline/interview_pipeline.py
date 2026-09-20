import logging
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel

from backend.models.interview import InterviewState, InterviewQuestion, InterviewAnswer
from backend.models.evidence import CandidateEvidence
from backend.agents.interview_agent import InterviewAgent

logger = logging.getLogger("hireflow.pipeline.interview")


class InterviewTurnResult(BaseModel):
    """Result of processing a single adaptive interview turn."""
    updated_state: InterviewState
    analyzed_answer: InterviewAnswer
    updated_evidence_map: Dict[str, CandidateEvidence]
    next_question: Optional[InterviewQuestion] = None
    is_completed: bool = False


def process_interview_answer(
    interview_state: InterviewState,
    current_question: InterviewQuestion,
    answer_text: str,
    current_evidence_map: Dict[str, CandidateEvidence],
    api_key: Optional[str] = None,
    force_mock: Optional[bool] = None,
) -> InterviewTurnResult:
    """
    Step 17: End-to-End Interview Turn Pipeline.
    Orchestrates:
      Answer -> Answer Analysis -> Evidence Extraction -> Requirement Update -> Gap Update -> Coverage Update -> Next Question Decision
    """
    agent = InterviewAgent(api_key=api_key, force_mock=force_mock, max_turns=interview_state.max_turns)

    # Ingest and analyze answer
    new_state, analyzed_answer, updated_evidence = agent.submit_answer(
        state=interview_state,
        question=current_question,
        candidate_answer=answer_text,
        current_evidence_map=current_evidence_map,
    )

    # Determine next question
    next_q = None
    if not new_state.is_completed:
        next_q = agent.get_next_question(new_state)
        if next_q is None:
            new_state.is_completed = True

    return InterviewTurnResult(
        updated_state=new_state,
        analyzed_answer=analyzed_answer,
        updated_evidence_map=updated_evidence,
        next_question=next_q,
        is_completed=new_state.is_completed,
    )
