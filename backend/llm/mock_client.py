import re
import json
import logging
from typing import Type, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel

from backend.llm.base import LLMClient
from backend.models.requirement import (
    JobRequirement,
    ExtractedRequirements,
    RequirementCategory,
)
from backend.models.candidate import (
    ResumeItem,
    ExtractedResumeData,
    ValidatedResumeExtraction,
)
from backend.models.evidence import (
    CandidateEvidence,
    Evidence,
    HistoryItem,
    RequirementRecord,
    ResumeEvaluationResult,
)
from backend.models.interview import (
    InterviewQuestion,
    InterviewAnswer,
    InterviewGap,
)
from backend.models.consistency import ConsistencyFlag
from backend.models.report import (
    RecruiterReport,
    RequirementEvaluationSummary,
    CoverageMetrics,
)

logger = logging.getLogger("hireflow.llm.mock")
T = TypeVar("T", bound=BaseModel)


class MockLLMClient(LLMClient):
    """
    Deterministic mock LLM client.
    Enables 100% offline development, testing, and deterministic evaluation without Gemini API keys.
    """

    def call_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        """Dispatches to deterministic schema-specific mock handlers."""
        if schema == ExtractedRequirements:
            return self._mock_extract_requirements(prompt)  # type: ignore
        elif schema in (ExtractedResumeData, ValidatedResumeExtraction):
            return self._mock_extract_resume(prompt)  # type: ignore
        elif schema == ResumeEvaluationResult:
            return self._mock_evaluate_resume(prompt)  # type: ignore
        elif schema == InterviewQuestion:
            return self._mock_generate_question(prompt)  # type: ignore
        elif schema == InterviewAnswer:
            return self._mock_analyze_answer(prompt)  # type: ignore
        elif schema == RecruiterReport:
            return self._mock_generate_report(prompt)  # type: ignore
        
        # Generic fallback for schema instantiation
        try:
            return schema.model_validate({})
        except Exception:
            return schema.model_construct()

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Returns deterministic text output based on prompt keywords."""
        if "summary" in prompt.lower():
            return "Candidate demonstrated strong backend Python proficiency and cloud deployment capability."
        return "Deterministic mock text response."

    # -------------------------------------------------------------------------
    # Schema Handlers
    # -------------------------------------------------------------------------

    def _mock_extract_requirements(self, prompt: str) -> ExtractedRequirements:
        """Deterministically extracts structured requirements from JD prompt."""
        jd_text = prompt
        if "<untrusted_content" in prompt:
            m = re.search(r"<untrusted_content[^>]*>(.*?)</untrusted_content>", prompt, re.DOTALL)
            if m:
                jd_text = m.group(1)
        elif "Job Description Data:" in prompt:
            jd_text = prompt.split("Job Description Data:", 1)[1]
        elif "Job Description:" in prompt:
            jd_text = prompt.split("Job Description:", 1)[1]

        lines = [l.strip() for l in jd_text.strip().splitlines() if l.strip()]
        reqs: List[JobRequirement] = []
        req_idx = 1

        for line in lines:
            if (
                line.startswith("#")
                or line.lower().startswith("about the role")
                or line.lower().startswith("job description")
                or line.lower().startswith("key requirements:")
                or line.lower().startswith("we are seeking")
                or line.lower().startswith("you will work")
            ):
                continue

            clean_line = re.sub(r"^[\d\.\-\*\•\)]+\s*", "", line).strip()
            if not clean_line or len(clean_line) < 15:
                continue

            # Anti-bias check
            if re.search(r"\b(gender|race|ethnic|ethnicity|age|marital|religion|sexual orientation|disability)\b", clean_line.lower()):
                continue

            # Determine must vs nice
            is_must = True
            if re.search(r"\[NICE\]|\(NICE\)|NICE:|preferred|bonus|plus|familiarity|nice to have", clean_line, re.IGNORECASE):
                is_must = False
            elif re.search(r"\[MUST\]|\(MUST\)|MUST:|required|mandatory|essential|minimum", clean_line, re.IGNORECASE):
                is_must = True
            else:
                is_must = (req_idx <= 4)

            # Determine category
            cat: RequirementCategory = "technical_skill"
            lower = clean_line.lower()
            if any(k in lower for k in ["year", "experience", "proven track record", "demonstrated history"]):
                cat = "experience"
            elif any(k in lower for k in ["degree", "bs", "ms", "bachelor", "master", "phd", "education"]):
                cat = "education"
            elif any(k in lower for k in ["lead", "mentor", "code review", "communication", "collaborate"]):
                cat = "responsibility" if "lead" in lower or "mentor" in lower else "soft_skill"
            elif any(k in lower for k in ["certified", "certification", "aws certified"]):
                cat = "certification"
            elif any(k in lower for k in ["fintech", "healthcare", "ecommerce", "domain", "compliance"]):
                cat = "domain_knowledge"

            # Extract keywords
            words = [w for w in re.findall(r"\b[A-Za-z0-9#\+\.]{3,}\b", clean_line) if w.lower() not in ["with", "have", "must", "nice", "years", "using", "work", "role"]]

            importance = "must" if is_must else "nice"
            weight = 2.0 if importance == "must" else 1.0

            reqs.append(
                JobRequirement(
                    id=f"REQ-{req_idx}",
                    category=cat,
                    requirement=clean_line,
                    importance=importance,
                    evidence_needed=f"Evidence demonstrating capability in: {clean_line[:60]}",
                    keywords=words[:5],
                    weight=weight,
                )
            )
            req_idx += 1

        if not reqs:
            reqs = [
                JobRequirement(id="REQ-1", category="experience", requirement="4+ years of professional backend software development experience using Python", importance="must", evidence_needed="Verified work history with Python backend systems", keywords=["Python", "Backend", "4+ years"], weight=2.0),
                JobRequirement(id="REQ-2", category="technical_skill", requirement="Production experience designing, building, and deploying RESTful APIs and distributed microservices", importance="must", evidence_needed="RESTful API endpoints and microservices architected", keywords=["REST", "API", "Microservices", "FastAPI"], weight=1.8),
                JobRequirement(id="REQ-3", category="technical_skill", requirement="Deep proficiency with relational databases (PostgreSQL or MySQL), complex schema design, indexing, and query optimization", importance="must", evidence_needed="Relational database schema design and query optimization evidence", keywords=["PostgreSQL", "MySQL", "Indexing", "Optimization"], weight=1.6),
                JobRequirement(id="REQ-4", category="technical_skill", requirement="Hands-on experience with asynchronous task processing and message brokers (e.g., Celery, RabbitMQ, or Apache Kafka)", importance="must", evidence_needed="Production message queue implementation", keywords=["Celery", "RabbitMQ", "Kafka"], weight=1.5),
                JobRequirement(id="REQ-5", category="technical_skill", requirement="Hands-on experience with containerization and orchestration using Docker and Kubernetes", importance="nice", evidence_needed="Docker containerization and Kubernetes deployment evidence", keywords=["Docker", "Kubernetes"], weight=1.0),
                JobRequirement(id="REQ-6", category="technical_skill", requirement="Familiarity with AWS cloud architecture (ECS, EKS, RDS, S3, and CloudWatch)", importance="nice", evidence_needed="AWS cloud deployment and monitoring evidence", keywords=["AWS", "ECS", "RDS", "CloudWatch"], weight=1.0),
                JobRequirement(id="REQ-7", category="responsibility", requirement="Demonstrated experience leading or mentoring junior engineering team members and conducting architectural code reviews", importance="nice", evidence_needed="Team leadership and code review participation", keywords=["Mentorship", "Code Reviews", "Leadership"], weight=1.0),
            ]

        return ExtractedRequirements(requirements=reqs)

    def _mock_extract_resume(self, prompt: str) -> ExtractedResumeData:
        """Deterministically extracts resume data with verbatim quote grounding."""
        raw_resume = prompt
        if "<untrusted_content" in prompt:
            m = re.search(r"<untrusted_content[^>]*>(.*?)</untrusted_content>", prompt, re.DOTALL)
            if m:
                raw_resume = m.group(1)
        elif "Resume Text:" in prompt:
            raw_resume = prompt.split("Resume Text:", 1)[1]
        elif "Candidate Resume Data:" in prompt:
            raw_resume = prompt.split("Candidate Resume Data:", 1)[1]

        skills: List[ResumeItem] = []
        experience: List[ResumeItem] = []
        projects: List[ResumeItem] = []
        qualifications: List[ResumeItem] = []

        lines = raw_resume.splitlines()
        current_section = "summary"

        for orig_line in lines:
            line_str = orig_line.strip()
            if not line_str:
                continue

            lower = line_str.lower()
            if "skill" in lower:
                current_section = "skills"
                if ":" in line_str and len(line_str.split(":", 1)[1].strip()) > 3:
                    quote_text = orig_line.strip()
                    skills_str = line_str.split(":", 1)[1]
                    for item in re.split(r"[,;•|]", skills_str):
                        clean_item = item.strip().strip("- ")
                        if clean_item and len(clean_item) > 1:
                            skills.append(ResumeItem(category="skills", title=clean_item, quote=quote_text))
                continue
            elif "experience" in lower or "employment" in lower or "work history" in lower:
                current_section = "experience"
                continue
            elif "project" in lower or "portfolio" in lower:
                current_section = "projects"
                continue
            elif "education" in lower or "qualification" in lower or "certification" in lower:
                current_section = "qualifications"
                continue
            elif "summary" in lower or "profile" in lower:
                current_section = "summary"
                continue

            clean_text = re.sub(r"^[\d\.\-\*\•\)]+\s*", "", line_str).strip()
            if len(clean_text) < 5:
                continue

            verbatim_quote = orig_line.strip()
            if verbatim_quote not in raw_resume:
                verbatim_quote = clean_text

            if current_section == "skills":
                if "," in clean_text:
                    for s in clean_text.split(","):
                        s_clean = s.strip().strip("- ")
                        if s_clean and len(s_clean) > 1:
                            skills.append(ResumeItem(category="skills", title=s_clean, quote=verbatim_quote))
                elif ":" in clean_text:
                    prefix, skill_items = clean_text.split(":", 1)
                    for s in skill_items.split(","):
                        s_clean = s.strip().strip("- ")
                        if s_clean and len(s_clean) > 1:
                            skills.append(ResumeItem(category="skills", title=f"{prefix.strip()}: {s_clean}", quote=verbatim_quote))
                else:
                    skills.append(ResumeItem(category="skills", title=clean_text, quote=verbatim_quote))
            elif current_section == "experience":
                experience.append(ResumeItem(category="experience", title=clean_text[:80], quote=verbatim_quote))
                if any(k in clean_text.lower() for k in ["architected", "built and maintained", "payment and reporting"]):
                    projects.append(ResumeItem(category="projects", title=clean_text[:80], quote=verbatim_quote))
            elif current_section == "projects":
                projects.append(ResumeItem(category="projects", title=clean_text[:80], quote=verbatim_quote))
            elif current_section in ["qualifications", "summary"]:
                if len(clean_text) > 15:
                    qualifications.append(ResumeItem(category="qualifications", title=clean_text[:80], quote=verbatim_quote))

        if not qualifications and len(lines) > 2:
            for l in lines:
                cl = l.strip()
                if len(cl) > 30 and not cl.startswith("#"):
                    qualifications.append(ResumeItem(category="qualifications", title=cl[:80], quote=cl))
                    break

        if not projects and experience:
            for exp in experience[:2]:
                projects.append(ResumeItem(category="projects", title=f"Project: {exp.title}", quote=exp.quote))

        return ExtractedResumeData(
            skills=skills,
            experience=experience,
            projects=projects,
            qualifications=qualifications,
        )

    def _mock_evaluate_resume(self, prompt: str) -> ResumeEvaluationResult:
        """Deterministically evaluates resume text against requirements."""
        reqs_raw: List[JobRequirement] = []
        resume_text = ""

        if "Job Requirements:" in prompt and "Candidate Resume Data:" in prompt:
            parts = prompt.split("Job Requirements:", 1)[1].split("Candidate Resume Data:", 1)
            reqs_part = parts[0].strip()
            resume_text = parts[1].strip()
            try:
                reqs_data = json.loads(reqs_part)
                for r in reqs_data:
                    req_text = r.get("requirement") or r.get("text", "")
                    imp = r.get("importance") or r.get("type", "must")
                    reqs_raw.append(JobRequirement(
                        id=r.get("id", "REQ-1"),
                        category=r.get("category", "technical_skill"),
                        requirement=req_text,
                        importance=imp,
                        weight=float(r.get("weight", 1.0)),
                    ))
            except Exception:
                pass
        elif "Job Requirements:" in prompt and "Resume Text:" in prompt:
            parts = prompt.split("Job Requirements:", 1)[1].split("Resume Text:", 1)
            try:
                reqs_data = json.loads(parts[0].strip())
                for r in reqs_data:
                    req_text = r.get("requirement") or r.get("text", "")
                    imp = r.get("importance") or r.get("type", "must")
                    reqs_raw.append(JobRequirement(
                        id=r.get("id", "REQ-1"),
                        category=r.get("category", "technical_skill"),
                        requirement=req_text,
                        importance=imp,
                        weight=float(r.get("weight", 1.0)),
                    ))
            except Exception:
                pass
            resume_text = parts[1].strip()
        else:
            resume_text = prompt

        if "<untrusted_content" in resume_text:
            m = re.search(r"<untrusted_content[^>]*>(.*?)</untrusted_content>", resume_text, re.DOTALL)
            if m:
                resume_text = m.group(1)

        if not reqs_raw:
            reqs_raw = [
                JobRequirement(id="REQ-1", category="experience", requirement="4+ years of professional backend software development experience using Python", importance="must", weight=2.0),
                JobRequirement(id="REQ-2", category="technical_skill", requirement="Production experience designing, building, and deploying RESTful APIs and distributed microservices", importance="must", weight=1.8),
                JobRequirement(id="REQ-3", category="technical_skill", requirement="Deep proficiency with relational databases (PostgreSQL or MySQL), complex schema design, indexing, and query optimization", importance="must", weight=1.6),
                JobRequirement(id="REQ-4", category="technical_skill", requirement="Hands-on experience with asynchronous task processing and message brokers (e.g., Celery, RabbitMQ, or Apache Kafka)", importance="must", weight=1.5),
                JobRequirement(id="REQ-5", category="technical_skill", requirement="Hands-on experience with containerization and orchestration using Docker and Kubernetes", importance="nice", weight=1.0),
                JobRequirement(id="REQ-6", category="technical_skill", requirement="Familiarity with AWS cloud architecture (ECS, EKS, RDS, S3, and CloudWatch)", importance="nice", weight=1.0),
                JobRequirement(id="REQ-7", category="responsibility", requirement="Demonstrated experience leading or mentoring junior engineering team members and conducting architectural code reviews", importance="nice", weight=1.0),
            ]

        records: List[RequirementRecord] = []
        resume_lower = resume_text.lower()
        resume_lines = [l.strip() for l in resume_text.splitlines() if l.strip()]

        is_strong_vague = "apex cloud systems" in resume_lower or "results-driven senior backend engineer" in resume_lower or "over 5 years" in resume_lower
        is_partial_fit = "bytecraft labs" in resume_lower or "passionate software developer with 3 years" in resume_lower

        for req in reqs_raw:
            req_text_lower = req.requirement.lower()
            ev_list: List[Evidence] = []
            status = "missing"
            confidence = "low"
            reason = ""

            if "python" in req_text_lower and any(y in req_text_lower for y in ["year", "experience", "4+", "5+", "proficiency"]):
                if is_strong_vague:
                    q = "Results-driven Senior Backend Engineer with over 5 years of experience building web applications and backend systems using Python and modern cloud tech."
                    actual_q = q if q in resume_text else [l for l in resume_lines if "python" in l.lower()][0]
                    status = "met"
                    confidence = "high"
                    reason = "Candidate has over 5 years of professional Python backend development experience."
                    ev_list.append(Evidence(source="resume", quote=actual_q))
                elif is_partial_fit:
                    q = "Passionate Software Developer with 3 years of engineering experience focusing on web application backends and API integration."
                    actual_q = q if q in resume_text else [l for l in resume_lines if "python" in l.lower()][0]
                    status = "partial"
                    confidence = "high"
                    reason = "Candidate has 3 years of software development experience, falling short of the required 4+ years."
                    ev_list.append(Evidence(source="resume", quote=actual_q))
                elif "python" in resume_lower:
                    p_lines = [l for l in resume_lines if "python" in l.lower()]
                    status = "partial"
                    confidence = "medium"
                    reason = "Python is mentioned in the resume without verified duration."
                    ev_list.append(Evidence(source="resume", quote=p_lines[0]))

            elif any(k in req_text_lower for k in ["api", "rest", "microservice", "distributed"]):
                if is_strong_vague:
                    q = "- Developed REST APIs and microservice endpoints with Python (FastAPI and Django)."
                    actual_q = q if q in resume_text else [l for l in resume_lines if "api" in l.lower()][0]
                    status = "met"
                    confidence = "high"
                    reason = "Production experience designing and building RESTful APIs and microservice endpoints."
                    ev_list.append(Evidence(source="resume", quote=actual_q))
                elif is_partial_fit:
                    q = "- Built and maintained RESTful API endpoints for internal dashboard services using Python and Flask."
                    actual_q = q if q in resume_text else [l for l in resume_lines if "api" in l.lower()][0]
                    status = "partial"
                    confidence = "medium"
                    reason = "Built REST endpoints for internal services, but lacks distributed microservices evidence."
                    ev_list.append(Evidence(source="resume", quote=actual_q))
                elif "api" in resume_lower:
                    p_lines = [l for l in resume_lines if "api" in l.lower()]
                    status = "partial"
                    confidence = "medium"
                    reason = "API endpoint development mentioned."
                    ev_list.append(Evidence(source="resume", quote=p_lines[0]))

            elif any(k in req_text_lower for k in ["database", "postgresql", "mysql", "sql", "relational", "schema", "indexing"]):
                if is_strong_vague:
                    q = "- Handled large volumes of transactions and optimized query performance across our database clusters."
                    actual_q = q if q in resume_text else "- Created relational database schemas and performed data migrations in PostgreSQL."
                    status = "unclear"
                    confidence = "medium"
                    reason = "High-level claims of query optimization without concrete metrics, schema design details, or indexing strategy."
                    ev_list.append(Evidence(source="resume", quote=actual_q if actual_q in resume_text else resume_lines[0]))
                elif is_partial_fit:
                    q = "- Designed relational schemas and wrote SQL queries for MySQL databases."
                    actual_q = q if q in resume_text else [l for l in resume_lines if "sql" in l.lower()][0]
                    status = "partial"
                    confidence = "medium"
                    reason = "Basic schema design and SQL query writing; lacks deep indexing and performance optimization."
                    ev_list.append(Evidence(source="resume", quote=actual_q))
                elif any(d in resume_lower for d in ["postgres", "mysql", "sql"]):
                    p_lines = [l for l in resume_lines if any(d in l.lower() for d in ["postgres", "mysql", "sql"])]
                    status = "partial"
                    confidence = "low"
                    reason = "Database mentioned without proof of optimization depth."
                    ev_list.append(Evidence(source="resume", quote=p_lines[0]))

            elif any(k in req_text_lower for k in ["asynchronous", "async", "celery", "rabbitmq", "kafka", "queue"]):
                if is_strong_vague:
                    q = "- Worked extensively with messaging technologies like RabbitMQ to handle asynchronous workloads."
                    actual_q = q if q in resume_text else [l for l in resume_lines if "rabbitmq" in l.lower()][0]
                    status = "met"
                    confidence = "high"
                    reason = "Extensive production experience using RabbitMQ for asynchronous workloads."
                    ev_list.append(Evidence(source="resume", quote=actual_q))
                elif is_partial_fit:
                    q = "Python, Flask, MySQL, Docker, Kubernetes, AWS, Apache Kafka, Celery, Redis, Elasticsearch, GraphQL"
                    actual_q = q if q in resume_text else resume_lines[0]
                    status = "unclear"
                    confidence = "low"
                    reason = "Celery/Kafka listed only under unverified self-study skills with explicit disclaimer."
                    ev_list.append(Evidence(source="resume", quote=actual_q))
                elif any(k in resume_lower for k in ["celery", "rabbitmq", "kafka", "queue"]):
                    p_lines = [l for l in resume_lines if any(k in l.lower() for k in ["celery", "rabbitmq", "kafka", "queue"])]
                    status = "unclear"
                    confidence = "medium"
                    reason = "Messaging technology mentioned without depth."
                    ev_list.append(Evidence(source="resume", quote=p_lines[0]))

            elif any(k in req_text_lower for k in ["docker", "kubernetes", "container"]):
                if is_strong_vague:
                    q = "- Automated system deployments using Docker containers and cloud infrastructure on AWS."
                    actual_q = q if q in resume_text else [l for l in resume_lines if "docker" in l.lower()][0]
                    status = "partial"
                    confidence = "medium"
                    reason = "Docker containerization in production, but Kubernetes orchestration details are absent."
                    ev_list.append(Evidence(source="resume", quote=actual_q))
                elif is_partial_fit:
                    q = "Python, Flask, MySQL, Docker, Kubernetes, AWS, Apache Kafka, Celery, Redis, Elasticsearch, GraphQL"
                    status = "unclear"
                    confidence = "low"
                    reason = "Docker and Kubernetes appear only in unverified self-study skills."
                    ev_list.append(Evidence(source="resume", quote=q if q in resume_text else resume_lines[0]))
                elif "docker" in resume_lower or "kubernetes" in resume_lower:
                    p_lines = [l for l in resume_lines if "docker" in l.lower() or "kubernetes" in l.lower()]
                    status = "partial"
                    confidence = "medium"
                    reason = "Container tooling mentioned."
                    ev_list.append(Evidence(source="resume", quote=p_lines[0]))

            elif any(k in req_text_lower for k in ["aws", "cloud", "ecs", "eks", "rds", "s3", "cloudwatch"]):
                if is_strong_vague:
                    q = "- Automated system deployments using Docker containers and cloud infrastructure on AWS."
                    actual_q = q if q in resume_text else [l for l in resume_lines if "aws" in l.lower()][0]
                    status = "unclear"
                    confidence = "medium"
                    reason = "Vague mention of 'cloud infrastructure on AWS' lacking specific ECS/RDS/CloudWatch architecture."
                    ev_list.append(Evidence(source="resume", quote=actual_q))
                elif is_partial_fit:
                    status = "missing"
                    confidence = "low"
                    reason = "No production AWS cloud experience found."
                elif "aws" in resume_lower:
                    p_lines = [l for l in resume_lines if "aws" in l.lower()]
                    status = "unclear"
                    confidence = "low"
                    reason = "AWS mentioned without specific architecture."
                    ev_list.append(Evidence(source="resume", quote=p_lines[0]))

            elif any(k in req_text_lower for k in ["lead", "mentor", "code review", "team"]):
                if is_strong_vague:
                    q = "- Mentored junior engineers and conducted regular team code reviews to ensure code quality."
                    actual_q = q if q in resume_text else [l for l in resume_lines if "mentor" in l.lower() or "lead" in l.lower()][0]
                    status = "met"
                    confidence = "high"
                    reason = "Experience leading teams, mentoring junior engineers, and conducting regular code reviews."
                    ev_list.append(Evidence(source="resume", quote=actual_q))
                elif is_partial_fit:
                    status = "missing"
                    confidence = "low"
                    reason = "No team leadership or code review experience."
                elif any(k in resume_lower for k in ["mentor", "lead", "review"]):
                    p_lines = [l for l in resume_lines if any(k in l.lower() for k in ["mentor", "lead", "review"])]
                    status = "partial"
                    confidence = "medium"
                    reason = "Collaboration or review mentioned."
                    ev_list.append(Evidence(source="resume", quote=p_lines[0]))
                else:
                    status = "missing"
                    confidence = "low"
                    reason = "No leadership or mentorship evidence found."

            else:
                words = [w for w in re.findall(r"\b\w{4,}\b", req_text_lower) if w not in ["experience", "years", "design", "building", "using", "with", "must", "nice"]]
                matched = [l for l in resume_lines if any(w in l.lower() for w in words)]
                if matched:
                    status = "partial"
                    confidence = "medium"
                    reason = f"Keyword matches found for: {', '.join(words[:2])}."
                    ev_list.append(Evidence(source="resume", quote=matched[0]))
                else:
                    status = "missing"
                    confidence = "low"
                    reason = "No relevant evidence identified."

            # Hard Rule 1 quote check
            valid_ev = [ev for ev in ev_list if ev.quote in resume_text]
            if not valid_ev and ev_list:
                for ev in ev_list:
                    for line in resume_lines:
                        if ev.quote.lower() in line.lower():
                            valid_ev.append(Evidence(source="resume", quote=line))
                            break

            records.append(
                RequirementRecord(
                    requirement_id=req.id,
                    status=status,
                    confidence=confidence,
                    evidence=valid_ev,
                    history=[
                        HistoryItem(
                            old_status=None,
                            new_status=status,
                            reason=reason or f"Assigned status '{status}' based on resume evidence.",
                        )
                    ],
                )
            )

        return ResumeEvaluationResult(records=records)

    def _mock_generate_question(self, prompt: str) -> InterviewQuestion:
        """Deterministically generates targeted interview questions."""
        req_id = "REQ-1"
        m_id = re.search(r"ID:\s*([A-Za-z0-9\-]+)", prompt)
        if m_id:
            req_id = m_id.group(1)

        req_text = "technical competency"
        m_req = re.search(r"Requirement:\s*([^\n]+)", prompt)
        if m_req:
            req_text = m_req.group(1).strip()

        is_follow_up = "Prior Question / Answer Context" in prompt and "None" not in prompt

        lower = req_text.lower()
        if "aws" in lower or "cloud" in lower:
            q_text = "Can you describe a production service you deployed to AWS, including how you configured ECS tasks, managed secrets, and monitored health with CloudWatch?"
            expected = "Details on AWS ECS deployment, container tasks, CloudWatch alarms, and RDS integration."
            purpose = "Verify hands-on production AWS architecture and deployment experience."
        elif "database" in lower or "postgres" in lower or "sql" in lower or "schema" in lower:
            q_text = "Can you walk me through a complex database query or indexing strategy you optimized in PostgreSQL or MySQL, including how you diagnosed slow execution using EXPLAIN ANALYZE?"
            expected = "Concrete discussion of B-tree/GIN indexes, query planning, connection pooling, and schema migration trade-offs."
            purpose = "Assess database indexing depth and performance optimization methodology."
        elif "asynchronous" in lower or "celery" in lower or "kafka" in lower or "rabbitmq" in lower:
            q_text = "How did you design your asynchronous message queues with RabbitMQ or Celery, and how did you handle message retries, idempotency, and dead-letter queues?"
            expected = "Demonstration of broker configuration, consumer scaling, idempotency keys, and error recovery."
            purpose = "Evaluate production asynchronous system architecture and resilience patterns."
        elif "docker" in lower or "kubernetes" in lower:
            q_text = "Can you detail your experience deploying containerized services to Kubernetes, specifically around Helm charts, resource limits, and rolling deployments?"
            expected = "Hands-on experience with Kubernetes manifests, pod auto-scaling, and rolling updates."
            purpose = "Assess container orchestration and production deployment capabilities."
        elif "lead" in lower or "mentor" in lower or "review" in lower:
            q_text = "Can you share an example of an architectural code review where you guided a junior engineer through refactoring a complex component?"
            expected = "Specific examples of mentorship, constructive code review standards, and technical leadership."
            purpose = "Verify technical leadership and mentoring capability."
        else:
            q_text = f"Could you provide a detailed technical walkthrough of your production experience with {req_text}?"
            expected = f"Concrete architecture, implementation specifics, and measurable outcomes for {req_text}."
            purpose = f"Assess practical production depth for {req_id}."

        if is_follow_up:
            q_text = f"Following up on your previous answer, could you provide specific architectural details on: {q_text}"

        return InterviewQuestion(
            question_id=f"Q-{req_id}",
            requirement_id=req_id,
            purpose=purpose,
            question=q_text,
            expected_evidence=expected,
            priority="HIGH",
            is_follow_up=is_follow_up,
        )

    def _mock_analyze_answer(self, prompt: str) -> InterviewAnswer:
        """Deterministically analyzes candidate answers against requirements."""
        req_id = "REQ-1"
        m_id = re.search(r"ID:\s*([A-Za-z0-9\-]+)", prompt)
        if m_id:
            req_id = m_id.group(1)

        answer_text = ""
        if "<untrusted_content" in prompt:
            m = re.search(r"<untrusted_content[^>]*>(.*?)</untrusted_content>", prompt, re.DOTALL)
            if m:
                answer_text = m.group(1).strip()
        elif "Candidate Answer Data:" in prompt:
            answer_text = prompt.split("Candidate Answer Data:", 1)[1].strip()

        lower_ans = answer_text.lower()

        # Check for strong vs weak evidence in answer
        is_strong = (
            len(answer_text) > 80
            and any(k in lower_ans for k in [
                "ecs", "cloudwatch", "fargate", "rds", "explain analyze", "btree", "composite index",
                "idempotent", "dead-letter", "dead letter", "rabbitmq", "celery", "helm",
                "horizontal pod", "10,000 req/sec", "50ms", "refactored", "code review checklist",
            ])
            and not any(w in lower_ans for w in ["mostly just watched", "haven't done it personally", "never used", "only read about"])
        )

        is_evasive = (
            len(answer_text) < 40
            or any(w in lower_ans for w in ["i don't know", "never used", "only basic", "not sure"])
            or "self-study only" in lower_ans
        )

        if is_strong:
            resolves_gap = True
            follow_up = False
            confidence = "high"
            evidence_found = answer_text[:150]
            reasoning = "Candidate provided concrete architectural specifics, production tooling, and technical metrics directly resolving the requirement gap."
        elif is_evasive:
            resolves_gap = False
            follow_up = False
            confidence = "low"
            evidence_found = None
            reasoning = "Candidate explicitly disclaimed production experience or gave an evasive answer without technical grounding."
        else:
            resolves_gap = False
            follow_up = True
            confidence = "medium"
            evidence_found = answer_text[:100] if len(answer_text) > 20 else None
            reasoning = "Candidate provided partial high-level concepts but lacked specific metrics, implementation depth, or concrete production examples."

        return InterviewAnswer(
            question_id=f"Q-{req_id}",
            requirement_id=req_id,
            answer=answer_text,
            evidence_found=evidence_found,
            confidence=confidence,
            resolves_gap=resolves_gap,
            follow_up_needed=follow_up,
            follow_up_focus="Probe for concrete production scale and metrics" if follow_up else None,
            reasoning=reasoning,
        )

    def _mock_generate_report(self, prompt: str) -> RecruiterReport:
        """Deterministically compiles structured recruiter report."""
        return RecruiterReport(
            report_id="REP-MOCK-001",
            candidate_id="CAND-001",
            coverage=CoverageMetrics(
                total_requirements=7,
                total_covered=6,
                coverage_percentage=0.857,
                must_have_total=4,
                must_have_covered=4,
                must_have_percentage=1.0,
                nice_to_have_total=3,
                nice_to_have_covered=2,
                nice_to_have_percentage=0.667,
            ),
            requirements_summary=[],
            unresolved_gaps=[],
            questions_asked=[],
            answers=[],
            consistency_flags=[],
            recruiter_notes=[
                "Candidate demonstrated 100% must-have requirement coverage upon interview completion.",
                "Strongest in Python backend engineering and relational database optimization.",
            ],
            executive_summary="Candidate possesses verified production experience across all mandatory technical requirements and successfully validated AWS and database gaps during the adaptive interview session.",
        )
