"""Test 5: Non-Answer Handling Test.

Section 6: An irrelevant answer leaves status unchanged and adds the requirement
to unanswered_areas.
"""

import os
from engine.llm import extract_requirements, map_candidate, analyze_answer

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "demo")


def test_non_answer_preservation():
    with open(os.path.join(DEMO_DIR, "jd.txt"), "r", encoding="utf-8") as f:
        jd_text = f.read()

    role = extract_requirements(jd_text)

    with open(os.path.join(DEMO_DIR, "resumes", "c2_hero.txt"), "r", encoding="utf-8") as f:
        resume_text = f.read()

    cand = map_candidate(role.requirements, resume_text, "Alex Rivera", "c2", "Candidate 2")

    docker_mapping = next(m for m in cand.mappings if m.requirement_id == "R3")
    original_status = docker_mapping.status

    # Irrelevant evasive answer
    irrelevant_answer = "Well, I really enjoy cooking Italian food on the weekends and playing pickleball with friends."
    question = "Can you describe how you configure and deploy Docker containers in production and CI/CD pipelines beyond local dev?"

    updated_cand = analyze_answer(cand, "R3", question, irrelevant_answer)

    updated_docker = next(m for m in updated_cand.mappings if m.requirement_id == "R3")
    assert updated_docker.status == original_status, f"Status should not change on non-answer: {updated_docker.status} != {original_status}"
    assert "R3" in updated_cand.unanswered_areas, "Requirement must be added to unanswered_areas"
    return True


if __name__ == "__main__":
    test_non_answer_preservation()
    print("PASS: test_non_answer_preservation")
