# ⚡ HireFlow: Evidence-Driven Interview Copilot

> **Pitch**: "HireFlow finds what a resume can't prove, helps the interviewer ask the right question, updates the evidence with what it learns, and shows exactly why. The AI surfaces evidence; humans make the decision."

HireFlow is an auditable, evidence-driven interview copilot that maps candidate claims to discrete requirements with **verbatim quote verification**, generates targeted probing questions, and dynamically updates evidence from live interview notes in **under 5 seconds**.

---

*(Note: HireFlow includes pre-computed deterministic golden caches and a sidebar **Demo Mode** toggle, ensuring 100% full-flow offline execution with zero network dependency.)*

---

## 5 Application Screens

1. **Screen 1: Role Setup**: Recruiter parses job descriptions, edits requirement text, tags `must_have` vs `nice_to_have`, and adds/removes criteria.
2. **Screen 2: Candidate Pool**: Qualitative fit buckets (`Strong Fit`, `Partial Fit`, `Needs Validation`) with "Why this bucket" breakdowns, status counts (`5 of 7 Clear`), consistency flag filters, Bias-Safe masking, and a cited recruiter Q&A assistant.
3. **Screen 3: Candidate Detail**: Deep-dive evidence inspector displaying verbatim source quotes, source tags (`resume` vs `interview`), consistency observations (overlapping dates, unbacked skills), and an immutable recruiter audit timeline.
4. **Screen 4: Interview Room (The Hero Loop)**: Note-taking interface with active targeted questions, a 1-click demo answer injection for Candidate 2, and real-time before/after status diffs (`Partial ➔ Clear`) in <5 seconds.
5. **Screen 5: Compare & Report**: Side-by-side candidate comparison matrix on identical criteria without ranking or declaring winners, plus an official PDF evidence report generator with human recruiter sign-off.

---

## Architecture & Hard Rules Compliance

- **R1 (No Scores/Verdict)**: No hire/reject recommendation, numeric match score, or declared winners. Statuses are discrete counts only.
- **R2 (Human Decision)**: Copilot assists interviewers with evidence; humans make the ultimate hiring decision.
- **R3 (Verbatim Quote Verifier)**: Substring matching in Python code normalizes whitespace and case. Any invented claim is downgraded to `Unclear`.
- **R4 (Missing Information)**: Absent information strictly defaults to `Missing` / `Not found in resume`.
- **R5 (Neutral Tone)**: Consistency flags use neutral phrasing (`"Dates overlap between X and Y, worth clarifying"`).
- **R6 (Fairness & Bias-Safe)**: PII and college names are stripped prior to mapping; UI toggle masks identities.
- **R7 (Status Schema)**: Allowed statuses: `Clear`, `Partial`, `Unclear`, `Missing`. Source tracked in `source` field.
- **R8 (Reliability & Cache)**: Temperature 0, strict JSON schema, disk caching by SHA-256 hash.
- **R9 (Prompt Injection Safety)**: Candidate text enclosed in inert data delimiters; immune to adversarial instructions.
