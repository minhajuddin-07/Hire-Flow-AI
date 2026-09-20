# HireFlow Technical Specification (Post-Audit v1.0)

## 1. System Architecture
HireFlow is built as a modular Python system with a clear separation of concerns:
- `engine/`: Core data structures, quote verification, anonymization, consistency rules, deterministic caching, and LLM calls.
- `data/`: Sample contracts, demo JDs, 6 golden candidate resumes, test edge cases, and pre-seeded disk cache.
- `app/`: Recruiter-grade Streamlit application featuring 5 key workflows: Role Setup, Candidate Pool, Candidate Detail, Interview Room, and Compare & Report.
- `tests/`: 10-point comprehensive automated verification harness executed via `python -m tests.run`.

## 2. Hard Rules (Enforced by Architecture & Tests)
- **R1 (No Scores/Verdict)**: No hire/reject recommendation, numeric match percentage, or declared winners. Statuses are strictly counts: e.g. `5 of 7 requirements Clear`.
- **R2 (Copilot Model)**: AI suggests targeted questions and tracks evidence; the human recruiter conducts the interview and inputs notes.
- **R3 (Verbatim Quote Verification)**: Every piece of evidence contains a verbatim quote verified against source text in Python code. If not found, `evidence=null`, `status=Unclear`, and audit warning logged.
- **R4 (Absent Data)**: Missing information defaults to `Missing` / `Not found in resume`.
- **R5 (Neutral Tone)**: Flags use neutral phrasing (`"Dates overlap between X and Y, worth clarifying"`).
- **R6 (Anonymization & Bias-Safe)**: Text sent to LLM has names, gender markers, contact info, and college names stripped. UI includes a global Bias-Safe toggle.
- **R7 (Status Vocabulary)**: Allowed requirement statuses: `Clear`, `Partial`, `Unclear`, `Missing`. Source tracked in `source` field (`resume` or `interview`).
- **R8 (Deterministic AI Execution)**: Temperature 0, strict JSON schema output, retry on parse error, SHA-256 disk caching. Instant Demo Mode runs offline.
- **R9 (Prompt Injection Immunity)**: Resumes are enclosed in inert data delimiters. Tested against prompt injection strings.

## 3. Data Schema Contract (`engine/schema.py`)
```python
class Requirement(BaseModel):
    id: str                 # e.g. "R1"
    text: str               # e.g. "3+ years professional Python backend experience"
    category: str           # "skill" | "experience" | "education" | "leadership"
    priority: str           # "must_have" | "nice_to_have"

class StatusChange(BaseModel):
    from_status: str        # e.g. "Partial"
    to_status: str          # e.g. "Clear"
    reason: str             # Explanation of why the evidence satisfied the criterion
    evidence: str           # Verbatim quote from interview notes
    source: str             # "interview"
    timestamp: str

class CandidateMapping(BaseModel):
    requirement_id: str
    status: str             # "Clear" | "Partial" | "Unclear" | "Missing"
    evidence: Optional[str] # Verbatim quote from source (or null)
    source: str             # "resume" | "interview"
    reasoning: str
    needs_validation: bool
    history: List[StatusChange] = []

class ConsistencyFlag(BaseModel):
    type: str               # "date_overlap" | "unbacked_skill" | "title_inflation"
    description: str        # Neutral explanation
    evidence: List[str]     # Quotes or dates involved

class AuditEntry(BaseModel):
    insight: str            # Action performed (e.g. "Docker status changed from Partial to Clear")
    requirement_id: Optional[str]
    inputs_used: str        # e.g. "Interview notes: 'Deployed containerized FastAPI microservices...'"
    model: str              # "gemini-2.5-flash" or "deterministic-engine"
    timestamp: str

class CandidateProfile(BaseModel):
    skills: List[Dict[str, str]]        # [{"skill": "Python", "quote": "..."}]
    experience: List[Dict[str, str]]    # [{"role": "...", "company": "...", "quote": "..."}]
    projects: List[Dict[str, str]]      # [{"name": "...", "quote": "..."}]
    education: List[Dict[str, str]]     # [{"degree": "...", "quote": "..."}]

class Candidate(BaseModel):
    id: str                             # e.g. "c1", "c2"
    name: str                           # e.g. "Alex Rivera"
    anon_label: str                     # e.g. "Candidate 2"
    stage: str                          # "screened" | "interviewed"
    summary: str
    profile: CandidateProfile
    mappings: List[CandidateMapping]
    gaps: List[str]
    interview_questions: List[Dict[str, str]] # [{"requirement_id": "R3", "question": "...", "follow_up": "..."}]
    flags: List[ConsistencyFlag]
    interview_log: List[Dict[str, str]]
    unanswered_areas: List[str]
    audit: List[AuditEntry]

class Role(BaseModel):
    id: str
    title: str
    requirements: List[Requirement]
```
