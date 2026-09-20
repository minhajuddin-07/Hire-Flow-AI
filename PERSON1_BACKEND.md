# Person 1 Backend & AI Agent Engine Documentation
## HireFlow AI — Production Backend & Intelligence System

**Author**: Person 1 (Backend & AI Engine Lead)  
**Target Audience**: Person 2 (Frontend / UI / Integration Lead), Evaluators, Developers  
**Version**: 1.0.0 (Hackathon 2026 Ready)  

---

## 1. System Overview

HireFlow is an AI Candidate Screening & Interview Intelligence Agent. The backend transforms raw, unstructured Job Descriptions and Resumes into structured, verifiable evidence maps, detects capability gaps, generates targeted technical interview questions, analyzes candidate answers in real time, updates requirement evidence dynamically, tracks interview coverage metrics, checks for cross-source consistency, and produces transparent recruiter reports.

---

## 2. Architecture & Directory Structure

```text
backend/
├── __init__.py
├── config.py                         # Environment config, mock flags, model defaults
│
├── models/                           # Strongly-typed Pydantic domain models
│   ├── __init__.py                   # Unified model exports
│   ├── job.py                        # JobPosting, JobRequirement, RequirementCategory
│   ├── candidate.py                  # Candidate, ValidatedResumeExtraction, ResumeItem
│   ├── requirement.py                # JobRequirement, Importance, EvidenceStatus
│   ├── evidence.py                   # CandidateEvidence, RequirementRecord, HistoryItem
│   ├── interview.py                  # InterviewGap, InterviewQuestion, InterviewAnswer, InterviewState
│   ├── consistency.py                # ConsistencyFlag, InconsistencyCategory, InconsistencySeverity
│   └── report.py                     # RecruiterReport, RequirementEvaluationSummary, CoverageMetrics
│
├── services/                         # Core domain logic and extraction engines
│   ├── __init__.py
│   ├── jd_parser.py                  # Step 4: JD Parsing & Categorization
│   ├── resume_parser.py              # Step 5: Resume Parsing & Verbatim Grounding (Hard Rule 1)
│   ├── requirement_mapper.py         # Step 5 & 8: Evidence Mapping & Dynamic Updates
│   ├── gap_detector.py               # Step 6: Gap Identification & Priority Ranking
│   ├── question_generator.py         # Step 7: Targeted Question & Follow-up Generation
│   ├── answer_analyzer.py            # Step 10: Technical Answer Analysis & Evidence Extraction
│   ├── coverage_tracker.py           # Step 9: Real-Time Coverage Metric Engine
│   ├── consistency_checker.py        # Step 11: Cross-Source Claim Verification
│   └── report_generator.py           # Step 18: Explainable Recruiter Report Generator
│
├── agents/                           # Autonomous conversational agents
│   ├── __init__.py
│   └── interview_agent.py            # Step 7: Adaptive Interview State Machine Agent
│
├── llm/                              # Isolated LLM abstraction layer
│   ├── __init__.py                   # Factory function & exports
│   ├── base.py                       # LLMClient interface & prompt injection sanitizer
│   ├── gemini_client.py              # Google GenAI SDK integration with error recovery
│   ├── mock_client.py                # 100% deterministic offline mock engine
│   └── prompts.py                    # Versioned, injection-guarded system prompts
│
├── pipeline/                         # High-level end-to-end workflows
│   ├── __init__.py
│   ├── screening_pipeline.py         # Step 17: screen_candidate() pipeline
│   └── interview_pipeline.py         # Step 17: process_interview_answer() pipeline
│
└── api/                              # Step 16: REST API Layer (FastAPI)
    ├── __init__.py
    ├── app.py                        # FastAPI application instance & CORS middleware
    └── routes.py                     # 11 Typed REST endpoints
```

---

## 3. Data Models Specification

### `JobRequirement`
- `id: str`: Unique requirement identifier (e.g., `"REQ-1"`)
- `category: RequirementCategory`: One of `technical_skill`, `experience`, `education`, `domain_knowledge`, `responsibility`, `certification`, `soft_skill`
- `requirement: str`: Description of required capability
- `importance: Literal["must", "nice"]`: Strict classification (`must` = mandatory, `nice` = preferred)
- `evidence_needed: str`: Concrete proof criteria
- `keywords: List[str]`: Technical and domain keywords
- `weight: float`: Weight multiplier (e.g. 1.5 - 2.0 for core must-haves)

### `CandidateEvidence`
- `requirement_id: str`: Target requirement ID
- `evidence: str`: Verbatim quote or extracted proof
- `source: Literal["resume", "interview"]`: Evidence origin
- `confidence: Literal["high", "medium", "low"]`: Evaluation confidence
- `status: Literal["CLEAR", "PARTIAL", "UNCLEAR", "MISSING"]`: Status indicator
- `reason: Optional[str]`: Objective justification

### `Candidate`
- `candidate_id: str`: Unique candidate identifier
- `resume_text: str`: Raw resume text
- `extracted_information: ValidatedResumeExtraction`: 100% verbatim-grounded resume entities
- `evidence_map: Dict[str, CandidateEvidence]`: Status and evidence per requirement
- `gaps: List[InterviewGap]`: Identified missing capabilities
- `consistency_flags: List[ConsistencyFlag]`: Diagnostic flags for unverified assertions

### `InterviewQuestion`
- `question_id: str`: Identifier (e.g. `"Q-REQ-1"`)
- `requirement_id: str`: Target requirement ID
- `purpose: str`: Diagnostic objective
- `question: str`: Targeted question text
- `expected_evidence: str`: Key technical details expected
- `priority: Literal["HIGH", "MEDIUM", "LOW"]`: Priority level
- `is_follow_up: bool`: Follow-up flag
- `parent_question_id: Optional[str]`: Prior question ID if follow-up

### `InterviewAnswer`
- `question_id: str`: Answered question ID
- `requirement_id: str`: Target requirement ID
- `answer: str`: Candidate's raw answer
- `evidence_found: Optional[str]`: Extracted evidence quote/summary
- `confidence: Literal["high", "medium", "low"]`: Evaluation confidence
- `resolves_gap: bool`: Whether the answer sufficiently proves capability
- `follow_up_needed: bool`: Whether deeper probing is necessary
- `follow_up_focus: Optional[str]`: Suggested angle if follow-up needed
- `reasoning: str`: Technical reasoning

### `InterviewState`
- `session_id: str`: Unique session identifier
- `job_requirements: List[JobRequirement]`: All requirements
- `covered_requirements: List[str]`: Requirement IDs with `CLEAR` status
- `unresolved_requirements: List[str]`: Requirement IDs with remaining gaps
- `questions_asked: List[InterviewQuestion]`: History of questions
- `answers: List[InterviewAnswer]`: History of analyzed answers
- `evidence_updates: List[CandidateEvidence]`: Dynamic combined evidence
- `coverage_percentage: float`: Overall coverage ratio (0.0 to 1.0)
- `must_have_coverage_percentage: float`: Must-have coverage ratio (0.0 to 1.0)
- `current_turn: int`: Number of turns elapsed
- `max_turns: int`: Session turn ceiling (default 5)
- `is_completed: bool`: Whether session has concluded

---

## 4. LLM Abstraction & Mock Mode

The backend isolates all generative AI dependencies behind the `LLMClient` interface.

### Automatic Mock Mode Fallback
- If `USE_MOCK_LLM=true` OR `GEMINI_API_KEY` is not provided, the system engages `MockLLMClient`.
- `MockLLMClient` executes fully deterministic heuristic algorithms matching the exact Pydantic output schemas, allowing offline unit testing and automated evaluation.

### Gemini Production Client
- Uses official Google GenAI SDK (`google.genai`).
- Enforces JSON Schema structured output mode (`response_schema=PydanticModel`).
- Catches validation errors and retries with explicit error feedback.
- If Gemini API quota or network fails, automatically falls back to `MockLLMClient` to prevent application crashes.

### Prompt Injection Defense
- Candidate resumes and interview answers are strictly treated as **untrusted data**.
- All untrusted inputs are passed through `sanitize_untrusted_input()`, neutralizing system prompt override phrases and enclosing input within `<untrusted_content is_untrusted_data="true">` boundaries.

---

## 5. End-to-End Pipelines

### 1. Initial Screening Pipeline (`screen_candidate`)
```python
from backend.pipeline import screen_candidate

result = screen_candidate(
    job_description=jd_text,
    resume=resume_text,
    candidate_id="CAND-001"
)

# Output contains:
# result.candidate: Candidate profile model
# result.job_requirements: Extracted requirements list
# result.evidence_map: Status and quotes per requirement
# result.gaps: Prioritized list of unresolved gaps
# result.consistency_flags: Flagged timeline/unsupported claims
# result.initial_coverage: Granular coverage breakdown
# result.suggested_initial_questions: Initial questions for top gaps
```

### 2. Adaptive Interview Agent Session
```python
from backend.agents import InterviewAgent
from backend.pipeline import process_interview_answer

agent = InterviewAgent(max_turns=5)
state = agent.initialize_session(
    requirements=result.job_requirements,
    initial_evidence_map=result.evidence_map,
    candidate_id="CAND-001"
)

# Ingest question & candidate answer
q = agent.get_next_question(state)
candidate_answer = "I architected our FastAPI services on AWS ECS..."

turn_result = process_interview_answer(
    interview_state=state,
    current_question=q,
    answer_text=candidate_answer,
    current_evidence_map=result.evidence_map
)

updated_state = turn_result.updated_state
updated_evidence_map = turn_result.updated_evidence_map
next_question = turn_result.next_question

# Finalize Recruiter Report
report = agent.finalize_report(
    state=updated_state,
    initial_evidence_map=result.evidence_map,
    final_evidence_map=updated_evidence_map,
    consistency_flags=result.consistency_flags
)
```

---

## 6. REST API Endpoints (FastAPI)

Run the FastAPI backend server:
```bash
uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --reload
```

| Method | Endpoint | Description | Request Body | Response Model |
|---|---|---|---|---|
| `GET` | `/health` | Health check | None | `{"status": "healthy"}` |
| `POST` | `/analyze-job` | Parse JD to structured criteria | `AnalyzeJobRequest` | `JobPosting` |
| `POST` | `/analyze-candidate` | Parse resume with quote validation | `AnalyzeCandidateRequest` | `ValidatedResumeExtraction` |
| `POST` | `/map-evidence` | Evaluate resume vs criteria | `MapEvidenceRequest` | `List[RequirementRecord]` |
| `POST` | `/detect-gaps` | Identify & rank requirement gaps | `DetectGapsRequest` | `List[InterviewGap]` |
| `POST` | `/generate-question` | Generate gap-targeted question | `GenerateQuestionRequest` | `InterviewQuestion` |
| `POST` | `/analyze-answer` | Analyze interview answer evidence | `AnalyzeAnswerRequest` | `InterviewAnswer` |
| `POST` | `/update-interview` | Advance interview turn & state | `UpdateInterviewRequest` | `InterviewTurnResult` |
| `POST` | `/check-consistency` | Cross-check claims & timeline | `CheckConsistencyRequest` | `List[ConsistencyFlag]` |
| `POST` | `/calculate-coverage` | Compute coverage statistics | `CalculateCoverageRequest` | `CoverageMetrics` |
| `POST` | `/generate-report` | Compile final recruiter report | `GenerateReportRequest` | `RecruiterReport` |
| `POST` | `/screen-candidate` | End-to-end screening pipeline | `ScreenCandidateRequest` | `ScreeningResult` |

---

## 7. How to Run & Test

### Running the Test Suite
```bash
pytest tests/test_backend_suite.py -v
```

### Running All Existing Integration Tests
```bash
python test_step0.py
python test_step1.py
python test_step2.py
python test_step3.py
python test_ui_and_persistence.py
```
