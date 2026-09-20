# HireFlow 3-Minute Timed Demo Script

**Total Run Time**: 2 minutes 50 seconds (leaves 10s buffer)  
**Persona**: Senior Recruiter & Technical Hiring Manager  
**Environment**: Streamlit App running locally (`http://localhost:8501`), Demo Mode enabled (offline-resilient).

---

### [0:00 – 0:30] Introduction & The Problem
- **Presenter**:
  > *"Every recruiting team faces the same dilemma: a candidate's resume says they 'know Docker' or 'worked with AWS', but paper can't prove production competency. The traditional response is either automated keyword screeners that reject great people, or subjective interviewer gut feelings.*
  > 
  > *HireFlow is fundamentally different: it is an **evidence-driven interview copilot**, not a resume screener. It finds what a resume can't prove, guides the interviewer with high-yield questions, updates the evidence in real time, and explains every conclusion with verified verbatim quotes. The AI surfaces evidence; humans make the hiring decision."*

---

### [0:30 – 1:00] Screen 1 & 2: Role Setup & The Candidate Pool
- **Action**: Start on **Screen 2: Candidate Pool**. Point to the sidebar:
  - Toggle **🛡️ Bias-Safe Mode** ON to demonstrate immediate masking of candidate names to `Candidate 1`, `Candidate 2`, etc.
  - Toggle **🛡️ Bias-Safe Mode** OFF to show candidate names.
- **Presenter**:
  > *"Notice right away what's NOT here: there are no numeric match percentages, no rankings, and no automated hire/reject labels—that violates our core ethical design.*
  > 
  > *Instead, we categorize candidates into qualitative fit buckets: **Strong Fit**, **Partial Fit**, and **Needs Validation** based purely on verified requirement counts. Let's expand 'Why this bucket?' for **Candidate 2 (Alex Rivera)**: Alex has 3 of 7 requirements Clear, but Docker is only Partial, and AWS is completely missing from the resume."*

---

### [1:00 – 1:30] Screen 3: Candidate Detail & Algorithmic Quote Verification
- **Action**: Switch to **Screen 3: Candidate Detail** (Alex Rivera selected).
- **Presenter**:
  > *"Let's inspect Alex's Requirement Evidence Map. When we expand Requirement R3 ('Docker in production/CI/CD'), notice the status is **Partial** (blue badge). Look at the verbatim quote: 'Used Docker for local development and running PostgreSQL locally'.*
  > 
  > *In HireFlow, every status claim must have a verbatim quote verified in Python code against the raw document. If an LLM hallucinates a claim not in the resume, our code rejects it, downgrades the status to Unclear, and logs an audit failure.*
  > 
  > *Because Alex's Docker experience is limited to local dev, HireFlow generates a targeted interview question: 'Can you describe how you configure and deploy Docker containers in production and CI/CD pipelines beyond local dev?'"*

---

### [1:30 – 2:15] Screen 4: Interview Room (The Hero Loop)
- **Action**: Switch to **Screen 4: Interview Room**.
  - Show the live **Evidence Coverage Bar**: `3 of 7 Requirements Clear (42%)`.
  - Point to the targeted Docker question.
  - Click **"⚡ Insert Demo Answer (Candidate 2 Docker Validation)"**.
  - The response appears in the interviewer notes textarea: *"I personally authored and maintained the multi-stage production Dockerfiles for our four FastAPI microservices. I configured our GitLab CI/CD runner to build, run vulnerability scans with Trivy, and push tagged container images to AWS ECR..."*
  - Click **"🚀 Analyze Answer & Update Evidence (Call C)"**.
- **Presenter**:
  > *"Now watch the magic in under 5 seconds. As an interviewer, I paste or type the candidate's actual answer and click Analyze.*
  > 
  > *Watch the screen: The status flips live from **Partial ➔ Clear** (green badge). The live Coverage Bar immediately updates from **42% ➔ 57%**.*
  > 
  > *Below, our Real-Time Evidence Feed records the exact state transition, the reason, and the new verbatim quote from the interview. Our immutable audit trail records the exact model, timestamp, and inputs used. We just validated in 3 seconds what a 2-page resume couldn't prove!"*

---

### [2:15 – 2:45] Screen 5: Multi-Candidate Comparison & Official PDF Report
- **Action**: Switch to **Screen 5: Compare & Report**.
  - Show the **Side-by-Side Requirement Evidence Matrix** (comparing Candidate 1, Candidate 2, and Candidate 3 side-by-side with verbatim quotes).
  - Switch to the **Recruiter Report** tab.
  - Show the Human Sign-off section and click **"📥 Download Official Recruiter PDF Report"**.
- **Presenter**:
  > *"Finally, in Screen 5, recruiters can compare 2 to 3 candidates side-by-side on identical requirement axes without declaring a winner.*
  > 
  > *Our generated report categorizes verified criteria, highlights remaining focus areas for the next round, and provides an official Human Sign-off box. One click downloads a formatted PDF evidence package.*
  > 
  > *HireFlow proves that AI in recruitment shouldn't replace human judgment—it should empower human interviewers with verified evidence."*

---

### [2:45 – 3:00] Wrap-up & Q&A Handoff
- **Presenter**:
  > *"Thank you! We're ready for judge questions."*
