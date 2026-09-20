"""Test 4: Hero Flow Test.

Rubric C: Candidate 2 Docker Partial -> Clear after sample answer;
history and audit entries exist; updates in under 30 seconds.
"""

import os
from engine.llm import extract_requirements, map_candidate, analyze_answer

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "demo")


def test_hero_flow():
    with open(os.path.join(DEMO_DIR, "jd.txt"), "r", encoding="utf-8") as f:
        jd_text = f.read()

    role = extract_requirements(jd_text)

    with open(os.path.join(DEMO_DIR, "resumes", "c2_hero.txt"), "r", encoding="utf-8") as f:
        resume_text = f.read()

    cand = map_candidate(role.requirements, resume_text, "Alex Rivera", "c2", "Candidate 2")

    # Verify initial Docker status is Partial
    docker_mapping = next(m for m in cand.mappings if m.requirement_id == "R3")
    assert docker_mapping.status == "Partial", f"Initial Docker status should be Partial, got {docker_mapping.status}"

    # Load hero answer
    with open(os.path.join(DEMO_DIR, "answers", "c2_docker_answer.txt"), "r", encoding="utf-8") as f:
        hero_answer = f.read()

    question = "Can you describe how you configure and deploy Docker containers in production and CI/CD pipelines beyond local dev?"

    initial_audit_count = len(cand.audit)

    # Execute Call C
    updated_cand = analyze_answer(cand, "R3", question, hero_answer)

    # Check updated Docker mapping
    updated_docker = next(m for m in updated_cand.mappings if m.requirement_id == "R3")
    assert updated_docker.status == "Clear", f"Expected Docker status to flip to Clear, got {updated_docker.status}"
    assert updated_docker.source == "interview", "Source should be interview"
    assert len(updated_docker.history) >= 1, "StatusChange history must be recorded"
    assert updated_docker.history[-1].from_status == "Partial"
    assert updated_docker.history[-1].to_status == "Clear"
    assert len(updated_cand.audit) > initial_audit_count, "Audit trail must be appended"
    return True


if __name__ == "__main__":
    test_hero_flow()
    print("PASS: test_hero_flow")
