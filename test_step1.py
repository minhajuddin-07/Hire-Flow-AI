import os
from pathlib import Path
from pipeline import extract_requirements
from audit import get_audit_trail

def test_extraction():
    sample_jd_path = Path(__file__).parent / "data" / "samples" / "job_description.txt"
    with open(sample_jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    print(f"Testing requirement extraction on sample JD ({len(jd_text)} chars)...")
    reqs = extract_requirements(jd_text)

    print(f"Extracted {len(reqs)} requirements:")
    for r in reqs:
        print(f" - [{r.id}] ({r.type.upper()}, weight={r.weight}) {r.text}")

    assert 5 <= len(reqs) <= 10, f"Expected around 7 requirements, got {len(reqs)}"
    
    types = {r.type for r in reqs}
    assert "must" in types, "Should have must-have requirements"
    assert "nice" in types, "Should have nice-to-have requirements"

    trail = get_audit_trail()
    assert len(trail) > 0
    latest = trail[-1]
    assert latest["step"] == "extract_requirements"
    assert len(latest["output"]) == len(reqs)

    print("\nALL STEP 1 PIPELINE TESTS PASSED!")

if __name__ == "__main__":
    test_extraction()
