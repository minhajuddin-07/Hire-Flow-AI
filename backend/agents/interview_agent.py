import uuid
import logging
from typing import List, Dict, Optional, Tuple

from backend.models.requirement import JobRequirement
from backend.models.evidence import CandidateEvidence
from backend.models.interview import (
    InterviewState,
    InterviewQuestion,
    InterviewAnswer,
    InterviewGap,
)
from backend.models.consistency import ConsistencyFlag
from backend.models.report import RecruiterReport
from backend.services.gap_detector import detect_gaps, get_next_unresolved_gap
from backend.services.question_generator import generate_interview_question
from backend.services.answer_analyzer import analyze_interview_answer
from backend.services.requirement_mapper import update_evidence_with_interview
from backend.services.coverage_tracker import calculate_coverage
from backend.services.report_generator import generate_recruiter_report
from backend.services.consistency_checker import check_consistency
from audit import log_entry

logger = logging.getLogger("hireflow.agents.interview_agent")


class InterviewAgent:
    """
    Step 7: Adaptive Interview Intelligence Agent.
    Manages the adaptive conversational state machine:
    1. Reads requirement & evidence map
    2. Identifies the highest priority unresolved gap
    3. Generates targeted technical interview questions
    4. Ingests and objectively analyzes candidate answers
    5. Dynamically updates evidence and coverage
    6. Decides whether to ask follow-up questions or progress to the next gap
    7. Continues until coverage target is achieved or turn limit reached.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        force_mock: Optional[bool] = None,
        max_turns: int = 5,
    ):
        self.api_key = api_key
        self.force_mock = force_mock
        self.max_turns = max_turns

    def initialize_session(
        self,
        requirements: List[JobRequirement],
        initial_evidence_map: Dict[str, CandidateEvidence],
        candidate_id: str = "CAND-001",
        session_id: Optional[str] = None,
    ) -> InterviewState:
        """Initializes a new adaptive interview session from initial screening results."""
        sid = session_id or f"SESS-{uuid.uuid4().hex[:8].upper()}"
        gaps = detect_gaps(requirements, initial_evidence_map)
        coverage = calculate_coverage(requirements, initial_evidence_map)

        covered_ids = [
            req.id
            for req in requirements
            if initial_evidence_map.get(req.id)
            and initial_evidence_map[req.id].status.upper() in ("CLEAR", "MET")
        ]
        unresolved_ids = [req.id for req in requirements if req.id not in covered_ids]

        # Initial evidence list
        evidence_list = list(initial_evidence_map.values())

        state = InterviewState(
            session_id=sid,
            candidate_id=candidate_id,
            job_requirements=requirements,
            covered_requirements=covered_ids,
            unresolved_requirements=unresolved_ids,
            gaps=gaps,
            questions_asked=[],
            answers=[],
            evidence_updates=evidence_list,
            coverage_percentage=coverage.coverage_percentage,
            must_have_coverage_percentage=coverage.must_have_percentage,
            current_turn=0,
            max_turns=self.max_turns,
            is_completed=len(unresolved_ids) == 0,
        )

        return state

    def get_next_question(self, state: InterviewState) -> Optional[InterviewQuestion]:
        """
        Determines and generates the next interview question based on current gaps and state.
        Returns None if session is complete or turn limit is reached.
        """
        if state.is_completed or state.current_turn >= state.max_turns:
            return None

        # 1. Check if the latest answer requires a follow-up
        if state.answers:
            latest_answer = state.answers[-1]
            if latest_answer.follow_up_needed and not latest_answer.resolves_gap:
                req = next((r for r in state.job_requirements if r.id == latest_answer.requirement_id), None)
                if req:
                    matching_gap = next((g for g in state.gaps if g.requirement_id == req.id), None)
                    if matching_gap:
                        q = generate_interview_question(
                            requirement=req,
                            gap=matching_gap,
                            previous_answers=state.answers,
                            api_key=self.api_key,
                            force_mock=self.force_mock,
                        )
                        return q

        # 2. Otherwise, pick the next highest priority unresolved gap
        already_asked_ids = [q.requirement_id for q in state.questions_asked]
        next_gap = get_next_unresolved_gap(state.gaps, already_asked_ids)

        if not next_gap:
            # All gaps have been probed at least once
            uncovered_gaps = [g for g in state.gaps if g.requirement_id in state.unresolved_requirements]
            if uncovered_gaps:
                next_gap = uncovered_gaps[0]
            else:
                return None

        req = next((r for r in state.job_requirements if r.id == next_gap.requirement_id), None)
        if not req:
            return None

        question = generate_interview_question(
            requirement=req,
            gap=next_gap,
            previous_answers=state.answers,
            api_key=self.api_key,
            force_mock=self.force_mock,
        )

        return question

    def submit_answer(
        self,
        state: InterviewState,
        question: InterviewQuestion,
        candidate_answer: str,
        current_evidence_map: Dict[str, CandidateEvidence],
    ) -> Tuple[InterviewState, InterviewAnswer, Dict[str, CandidateEvidence]]:
        """
        Processes a candidate's answer to an interview question:
        1. Analyzes answer for technical evidence
        2. Updates requirement status and dynamic evidence
        3. Recalculates coverage metrics
        4. Updates session state and checks completion
        """
        req = next((r for r in state.job_requirements if r.id == question.requirement_id), None)
        if not req:
            raise ValueError(f"Requirement '{question.requirement_id}' not found in interview session.")

        # Analyze answer
        analyzed_answer = analyze_interview_answer(
            question=question,
            requirement=req,
            candidate_answer=candidate_answer,
            api_key=self.api_key,
            force_mock=self.force_mock,
        )

        # Update evidence
        updated_evidence_map = dict(current_evidence_map)
        new_status = "CLEAR" if analyzed_answer.resolves_gap else "PARTIAL"

        interview_evidence = CandidateEvidence(
            requirement_id=req.id,
            evidence=analyzed_answer.evidence_found or candidate_answer[:150],
            source="interview",
            confidence=analyzed_answer.confidence,
            status=new_status,
            reason=analyzed_answer.reasoning,
        )

        updated_evidence_map = update_evidence_with_interview(
            updated_evidence_map, interview_evidence
        )

        # Recalculate coverage and gaps
        new_coverage = calculate_coverage(state.job_requirements, updated_evidence_map)
        remaining_gaps = detect_gaps(state.job_requirements, updated_evidence_map)

        new_covered_ids = [
            r.id
            for r in state.job_requirements
            if updated_evidence_map.get(r.id)
            and updated_evidence_map[r.id].status.upper() in ("CLEAR", "MET")
        ]
        new_unresolved_ids = [
            r.id for r in state.job_requirements if r.id not in new_covered_ids
        ]

        new_turn = state.current_turn + 1
        is_done = (
            len(new_unresolved_ids) == 0
            or new_turn >= state.max_turns
            or new_coverage.must_have_percentage >= 1.0
        )

        updated_state = InterviewState(
            session_id=state.session_id,
            candidate_id=state.candidate_id,
            job_requirements=state.job_requirements,
            covered_requirements=new_covered_ids,
            unresolved_requirements=new_unresolved_ids,
            gaps=remaining_gaps,
            questions_asked=state.questions_asked + [question],
            answers=state.answers + [analyzed_answer],
            evidence_updates=list(updated_evidence_map.values()),
            coverage_percentage=new_coverage.coverage_percentage,
            must_have_coverage_percentage=new_coverage.must_have_percentage,
            current_turn=new_turn,
            max_turns=state.max_turns,
            is_completed=is_done,
        )

        insight_id = f"INSIGHT-TURN-{uuid.uuid4().hex[:8].upper()}"
        log_entry(
            insight_id=insight_id,
            step="process_interview_turn",
            inputs_used=[
                {
                    "session_id": state.session_id,
                    "turn": new_turn,
                    "question_id": question.question_id,
                    "requirement_id": question.requirement_id,
                }
            ],
            prompt_version="v1",
            output={
                "answer_analysis": analyzed_answer.model_dump(),
                "new_coverage": new_coverage.model_dump(),
            },
        )

        return updated_state, analyzed_answer, updated_evidence_map

    def finalize_report(
        self,
        state: InterviewState,
        initial_evidence_map: Dict[str, CandidateEvidence],
        final_evidence_map: Dict[str, CandidateEvidence],
        consistency_flags: Optional[List[ConsistencyFlag]] = None,
    ) -> RecruiterReport:
        """Generates the final comprehensive RecruiterReport."""
        return generate_recruiter_report(
            candidate_id=state.candidate_id,
            requirements=state.job_requirements,
            initial_evidence_map=initial_evidence_map,
            final_evidence_map=final_evidence_map,
            interview_state=state,
            consistency_flags=consistency_flags,
        )
