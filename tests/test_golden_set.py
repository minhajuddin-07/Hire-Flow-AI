"""Test 3: Golden Set Evaluation.

Rubric F: On the golden set (6 demo candidates), statuses match expected values
in >= 90% of cases.
"""

import os
import json
from engine.llm import extract_requirements, map_candidate

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "demo")


def test_golden_set_accuracy():
    with open(os.path.join(DEMO_DIR, "jd.txt"), "r", encoding="utf-8") as f:
        jd_text = f.read()

    role = extract_requirements(jd_text)

    with open(os.path.join(DEMO_DIR, "expected.json"), "r", encoding="utf-8") as f:
        expected = json.load(f)

    candidates = [
        ("c1", "Sarah Chen", "c1_strong.txt"),
        ("c2", "Alex Rivera", "c2_hero.txt"),
        ("c3", "Marcus Vance", "c3_thin_leadership.txt"),
        ("c4", "Elena Rostova", "c4_date_overlap.txt"),
        ("c5", "David Kim", "c5_unbacked_skill.txt"),
        ("c6", "Priya Patel", "c6_messy_format.txt")
    ]

    total_evals = 0
    matched_evals = 0
    discrepancies = []

    for cid, cname, fname in candidates:
        rpath = os.path.join(DEMO_DIR, "resumes", fname)
        with open(rpath, "r", encoding="utf-8") as f:
            rtext = f.read()

        cand = map_candidate(role.requirements, rtext, cname, cid, f"Candidate {cid[1]}")
        c_expected = expected.get(cid, {})

        for m in cand.mappings:
            total_evals += 1
            exp_status = c_expected.get(m.requirement_id)
            if m.status == exp_status:
                matched_evals += 1
            else:
                discrepancies.append(f"{cid} {m.requirement_id}: got {m.status}, expected {exp_status}")

    accuracy_pct = (matched_evals / total_evals) * 100.0 if total_evals > 0 else 0
    assert accuracy_pct >= 90.0, f"Accuracy {accuracy_pct:.1f}% below 90% threshold. Discrepancies: {discrepancies}"
    return accuracy_pct


if __name__ == "__main__":
    acc = test_golden_set_accuracy()
    print(f"PASS: test_golden_set_accuracy: {acc:.1f}% match")
