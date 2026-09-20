# Person 1 Backend Architecture Document
## HireFlow AI — AI Candidate Screening & Interview Intelligence Engine

**Author**: Person 1 (Backend & AI Agent Lead)  
**Project**: HireFlow AI Agent Hackathon 2026  
**Status**: Architecture Baseline & Design Specification  

---

## 1. Executive Summary

HireFlow is an end-to-end AI candidate screening and adaptive interview intelligence agent. It translates unstructured Job Descriptions and Resumes into verifiable, evidence-backed hiring insights and dynamically conducts structured interview sessions.

### Core Processing Flow:
$$\text{Job Description} + \text{Resume} \longrightarrow \text{Requirement Extraction} \longrightarrow \text{Evidence Mapping} \longrightarrow \text{Gap Detection} \longrightarrow \text{Targeted Interview Questions} \longrightarrow \text{Answer Analysis} \longrightarrow \text{Evidence Update} \longrightarrow \text{Interview Coverage Tracking} \longrightarrow \text{Final Recruiter Report}$$

---

## 2. Current Project State & Inspection Findings

### Workspace Layout
- `app.py`: Streamlit frontend implementing initial UI prototypes for Steps 0–3.
- `models.py`: Preliminary Pydantic models (`Requirement`, `Evidence`, `HistoryItem`, `RequirementRecord`, `ExtractedRequirements`, `ResumeItem`, `ExtractedResumeData`, `ValidatedResumeExtraction`, `ResumeEvaluationResult`).
- `pipeline.py`: Basic functions for `extract_requirements`, `validate_quote`, `extract_resume_profile`, and `evaluate_resume_requirements`.
- `llm.py`: Direct Google GenAI API client integration with embedded heuristic fallback parsers for offline/unauthenticated execution.
- `audit.py`: JSON-based append-only audit trail logger (`data/audit.json`).
- `data/samples/`: Test fixtures including `job_description.txt`, `resume_strong_vague.txt`, `resume_partial_fit.txt`, and interview answer samples.
- `test_step0.py`, `test_step1.py`, `test_step2.py`, `test_step3.py`, `test_ui_and_persistence.py`: Initial test scripts.

### What Already Works
- Heuristic and Gemini extraction for Job Description requirements.
- Resume profile extraction with Hard Rule 1 (Verbatim Quote Validator).
- Mapping resume evidence to requirements with initial statuses (`met`, `partial`, `unclear`, `missing`).
- Basic local audit logging to `data/audit.json`.

### What Is Missing (Production-Grade Backend Requirements)
1. **Modular Backend Hierarchy**: Proper `backend/` package containing distinct domains (`models/`, `services/`, `agents/`, `llm/`, `pipeline/`, `api/`).
2. **Complete Data Models (Step 3)**:
   - Typed models: `JobRequirement`, `CandidateEvidence` (`CLEAR`, `PARTIAL`, `UNCLEAR`, `MISSING`), `Candidate`, `InterviewQuestion`, `InterviewAnswer`, `InterviewState`, `ConsistencyFlag`, `RecruiterReport`.
3. **Advanced Backend Services (Steps 4–11)**:
   - `jd_parser.py`: Multi-category taxonomy (technical skill, experience, education, domain knowledge, responsibility, certification, soft skill), required vs. preferred segregation, keyword extraction.
   - `resume_parser.py`: Verbatim grounding, anti-hallucination validation, structured entity extraction.
   - `requirement_mapper.py`: Grounded status assignment with strict quote validation.
   - `gap_detector.py`: Priority-ranked gap detection based on requirement importance and missing evidence.
   - `question_generator.py`: Tailored technical and behavioral interview question generator focusing on specific unresolved gaps.
   - `answer_analyzer.py`: Objective evidence extractor from interview transcripts, checking gap resolution and follow-up necessity.
   - `coverage_tracker.py`: Real-time coverage metrics (% must-haves covered, % total requirements covered, unresolved matrix).
   - `consistency_checker.py`: Cross-source timeline and claim verification (resume claims vs. interview answers vs. verified evidence) with neutral diagnostic flags.
   - `report_generator.py`: Transparent, explainable recruiter report generation without opaque single-number scores.
4. **Adaptive Interview Agent (Step 7)**:
   - State machine executing iterative question generation $\to$ candidate answer ingestion $\to$ evidence synthesis $\to$ gap resolution $\to$ follow-up question decisions.
5. **LLM Abstraction & Security Layer (Steps 12–15)**:
   - `LLMClient` interface with concrete `GeminiClient` and deterministic `MockLLMClient`.
   - Schema validation recovery and strict JSON output parsing.
   - Anti-prompt-injection sanitization treating untrusted candidate inputs as isolated data.
6. **FastAPI Service & End-to-End Pipelines (Steps 16–17)**:
   - REST API exposing all engine capabilities.
   - High-level pipeline entry points (`screen_candidate`, `process_interview_answer`).
7. **Comprehensive Unit & Integration Test Suite (Step 19)**:
   - Dedicated test suite validating all 14 required capabilities.

---

## 3. Architecture Specification

```
backend/
├── __init__.py
├── config.py                         # Environment config, mock flags, model defaults
├── models/
│   ├── __init__.py                   # Unified export of all domain models
│   ├── job.py                        # JobRequirement, JobPosting, RequirementCategory
│   ├── candidate.py                  # Candidate, CandidateProfile, ExtractedInfo
│   ├── requirement.py                # RequirementStatus, Importance, RequirementDefinition
│   ├── evidence.py                   # CandidateEvidence, EvidenceSource, VerificationStatus
│   ├── interview.py                  # InterviewQuestion, InterviewAnswer, InterviewState
│   ├── consistency.py                # ConsistencyFlag, InconsistencyType, TimelineClaim
│   └── report.py                     # RecruiterReport, RequirementSummary, AuditSummary
│
├── services/
│   ├── __init__.py
│   ├── jd_parser.py                  # Step 4: JD Parsing & Categorization
│   ├── resume_parser.py              # Step 5: Resume Parsing & Verbatim Grounding
│   ├── requirement_mapper.py         # Step 5 & 8: Evidence Mapping
│   ├── gap_detector.py               # Step 6: Gap Identification & Prioritization
│   ├── question_generator.py         # Step 7: Targeted Question Generation
│   ├── answer_analyzer.py            # Step 10: Answer Analysis & Evidence Extraction
│   ├── coverage_tracker.py           # Step 9: Live Coverage & Metric Tracking
│   ├── consistency_checker.py        # Step 11: Cross-Source Claim Verification
│   └── report_generator.py           # Step 18: Structured Recruiter Report Engine
│
├── agents/
│   ├── __init__.py
│   └── interview_agent.py            # Step 7: Adaptive Interview State Machine Agent
│
├── llm/
│   ├── __init__.py
│   ├── base.py                       # LLMClient interface & prompt injection guardrails
│   ├── gemini_client.py              # Google GenAI implementation with schema validation
│   ├── mock_client.py                # Deterministic mock client for offline tests
│   └── prompts.py                    # Versioned system prompts with security boundaries
│
├── pipeline/
│   ├── __init__.py
│   ├── screening_pipeline.py         # Step 17: End-to-end candidate screening
│   └── interview_pipeline.py         # Step 17: End-to-end interview turn processing
│
└── api/
    ├── __init__.py
    ├── app.py                        # FastAPI application instance & middleware
    └── routes.py                     # REST endpoints (Step 16)
```

---

## 4. File Modification & Creation Matrix

### Files to Create
| File Path | Purpose |
|---|---|
| `backend/config.py` | Configuration settings (`GEMINI_API_KEY`, `USE_MOCK_LLM`, model name) |
| `backend/models/*.py` | Pydantic data models for Job, Candidate, Evidence, Interview, Consistency, Report |
| `backend/services/*.py` | Domain services for parsing, mapping, gaps, questions, answers, coverage, consistency, reports |
| `backend/agents/interview_agent.py` | Adaptive conversational agent loop |
| `backend/llm/*.py` | Clean LLM interface, Gemini client, deterministic mock client, prompt templates |
| `backend/pipeline/*.py` | Screening and interview workflow orchestrators |
| `backend/api/*.py` | FastAPI application and route definitions |
| `tests/test_backend_suite.py` | Comprehensive test suite covering Tests 1–14 |
| `PERSON1_BACKEND.md` | Full documentation for backend architecture, APIs, and configuration |
| `PERSON1_MERGE_NOTES.md` | Merge instructions, compatibility guarantees, and integration steps for Person 2 |

### Files to Maintain / Adapt for Backward Compatibility
| File Path | Strategy |
|---|---|
| `models.py` | Maintain full backward compatibility for existing `app.py` imports, while bridging to `backend.models` |
| `pipeline.py` | Maintain backward compatibility for `extract_requirements`, `extract_resume_profile`, `evaluate_resume_requirements`, bridging to `backend.pipeline` |
| `llm.py` | Maintain existing helper signatures while routing through `backend.llm` |
| `audit.py` | Keep audit trail logger intact |
| `app.py` | **DO NOT MODIFY** Person 2 UI architecture; ensure all imports continue to succeed seamlessly |
| `requirements.txt` | Ensure required dependencies (`fastapi`, `pytest`, `uvicorn`, `streamlit`, `google-genai`, `pydantic`, `python-dotenv`) are listed |

---

## 5. Integration Points for Person 2

Person 2 can integrate with the backend in two ways:

### 1. Direct Python Package Import (In-Process Integration)
```python
from backend.pipeline.screening_pipeline import screen_candidate
from backend.pipeline.interview_pipeline import process_interview_answer
from backend.agents.interview_agent import InterviewAgent
from backend.services.report_generator import generate_recruiter_report

# Run initial candidate screening:
screening_result = screen_candidate(jd_text, resume_text)

# Run interactive adaptive interview:
agent = InterviewAgent()
state = agent.initialize(screening_result)
next_q = agent.get_next_question(state)
state = agent.submit_answer(state, candidate_answer)
report = agent.finalize_report(state)
```

### 2. FastAPI REST Endpoints (Microservice Integration)
```http
POST /analyze-job
POST /analyze-candidate
POST /map-evidence
POST /detect-gaps
POST /generate-question
POST /analyze-answer
POST /update-interview
POST /check-consistency
POST /calculate-coverage
POST /generate-report
POST /screen-candidate
GET  /health
```

---

## 6. Verification and Git Safety Plan
- Create and switch to branch `person1`.
- Run comprehensive test suite validating all 14 required capabilities.
- Ensure 0 regression on existing test files (`test_step0.py` through `test_step3.py`).
- Verify no secrets or credentials are in git history.
- Commit changes cleanly under `Person 1: build HireFlow AI backend and agent engine`.
