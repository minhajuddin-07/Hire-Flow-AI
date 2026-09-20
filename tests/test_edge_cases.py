"""Test 9: Edge Cases and Graceful Degradation Test.

Section 6: Empty resume, empty notes, missing requirement, API failure -> graceful.
"""

from engine.schema import Requirement
from engine.llm import map_candidate, analyze_answer, extract_requirements
from engine.consistency import check_consistency_flags
from engine.schema import CandidateProfile


def test_empty_resume_handling():
    reqs = [
        Requirement(id="R1", text="Python 3+ years", category="skill", priority="must_have"),
        Requirement(id="R2", text="FastAPI", category="skill", priority="must_have")
    ]
    cand = map_candidate(reqs, "", "Test Candidate", "c_empty", "Candidate Empty")
    assert cand is not None
    assert len(cand.mappings) == 2
    for m in cand.mappings:
        assert m.status == "Missing"
        assert m.evidence is None
    return True


def test_empty_notes_handling():
    reqs = [Requirement(id="R1", text="Python", category="skill", priority="must_have")]
    cand = map_candidate(reqs, "Experienced with Python", "Test Candidate", "c_test")
    # Call analyze_answer with empty answer
    updated = analyze_answer(cand, "R1", "What did you build?", "")
    assert updated is not None
    assert len(updated.interview_log) == 1
    return True


def test_empty_jd_handling():
    role = extract_requirements("")
    assert role is not None
    assert role.id == "role_empty"
    return True


def test_consistency_flags():
    profile = CandidateProfile(
        experience=[
            {"role": "Lead", "company": "Company A", "period": "2022 - Present", "quote": "Worked at Company A"},
            {"role": "Senior", "company": "Company B", "period": "2021 - 2023", "quote": "Worked at Company B"}
        ],
        skills=[
            {"skill": "Kubernetes", "quote": "Kubernetes"}
        ]
    )
    flags = check_consistency_flags(profile, "Raw resume text without projects")
    assert len(flags) >= 1
    flag_types = [f.type for f in flags]
    assert "date_overlap" in flag_types or "unbacked_skill" in flag_types
    return True


if __name__ == "__main__":
    test_empty_resume_handling()
    test_empty_notes_handling()
    test_empty_jd_handling()
    test_consistency_flags()
    print("PASS: test_edge_cases")
