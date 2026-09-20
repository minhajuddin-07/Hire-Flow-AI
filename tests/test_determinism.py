"""Test 2: Determinism Test.

Rule R8 & Rubric F: Run the same candidate 3 times; outputs must be identical.
"""

import os
from engine.llm import extract_requirements, map_candidate

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "demo")


def test_determinism_three_runs():
    with open(os.path.join(DEMO_DIR, "jd.txt"), "r", encoding="utf-8") as f:
        jd_text = f.read()

    role = extract_requirements(jd_text)

    with open(os.path.join(DEMO_DIR, "resumes", "c2_hero.txt"), "r", encoding="utf-8") as f:
        resume_text = f.read()

    run1 = map_candidate(role.requirements, resume_text, "Alex Rivera", "c2", "Candidate 2")
    run2 = map_candidate(role.requirements, resume_text, "Alex Rivera", "c2", "Candidate 2")
    run3 = map_candidate(role.requirements, resume_text, "Alex Rivera", "c2", "Candidate 2")

    statuses1 = [m.status for m in run1.mappings]
    statuses2 = [m.status for m in run2.mappings]
    statuses3 = [m.status for m in run3.mappings]

    assert statuses1 == statuses2 == statuses3, f"Outputs not deterministic: {statuses1} vs {statuses2} vs {statuses3}"

    quotes1 = [m.evidence for m in run1.mappings]
    quotes2 = [m.evidence for m in run2.mappings]
    quotes3 = [m.evidence for m in run3.mappings]

    assert quotes1 == quotes2 == quotes3, f"Evidence quotes not deterministic across 3 runs"
    return True


if __name__ == "__main__":
    test_determinism_three_runs()
    print("PASS: test_determinism_three_runs")
