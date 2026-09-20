import os
from pathlib import Path
from pipeline import extract_resume_profile, validate_quote
from audit import get_audit_trail
from models import ValidatedResumeExtraction

def test_resume_extraction():
    samples_dir = Path(__file__).parent / "data" / "samples"
    resume_files = ["resume_partial_fit.txt", "resume_strong_vague.txt"]

    for filename in resume_files:
        filepath = samples_dir / filename
        with open(filepath, "r", encoding="utf-8") as f:
            resume_text = f.read()

        print(f"\n--- Testing Resume Extraction on: {filename} ({len(resume_text)} chars) ---")
        validated: ValidatedResumeExtraction = extract_resume_profile(resume_text)

        print(f"Extracted Total: {validated.total_extracted}, Valid: {validated.total_valid}, Dropped: {validated.dropped_count}")
        print(f"Skills: {len(validated.skills)}")
        print(f"Experience: {len(validated.experience)}")
        print(f"Projects: {len(validated.projects)}")
        print(f"Qualifications: {len(validated.qualifications)}")

        # Verification 1: Categories must be populated
        assert len(validated.skills) > 0, "Should have extracted skills"
        assert len(validated.experience) > 0, "Should have extracted experience"
        assert len(validated.projects) > 0, "Should have extracted projects"
        assert len(validated.qualifications) > 0, "Should have extracted qualifications"

        # Verification 2 (CHECK): Every single displayed quote MUST be found exactly in the resume text
        all_items = (
            validated.skills
            + validated.experience
            + validated.projects
            + validated.qualifications
        )

        for item in all_items:
            assert item.quote in resume_text, (
                f"Hard Rule 1 Check Failed: Quote '{item.quote}' not found in resume text!"
            )

        print("[CHECK PASSED] 100% of displayed quotes are exact verbatim substrings in the resume text.")

    # Verification 3: Test Hard Rule 1 quote validator directly against manipulated/hallucinated quotes
    dummy_text = "Experienced Senior Python Engineer with 6 years building distributed APIs in Django and FastAPI."
    
    # Valid quote
    valid_res = validate_quote("building distributed APIs in Django and FastAPI", dummy_text)
    assert valid_res is not None
    assert valid_res in dummy_text

    # Hallucinated quote
    invalid_res = validate_quote("10+ years architecting Kubernetes on AWS", dummy_text)
    assert invalid_res is None, "Validator must reject quotes not present in source text"

    # Verification 4: Audit trail
    trail = get_audit_trail()
    assert len(trail) > 0
    latest = trail[-1]
    assert latest["step"] == "extract_resume"
    assert "skills" in latest["output"]

    print("\nALL STEP 2 PIPELINE & HARD RULE 1 TESTS PASSED!")

if __name__ == "__main__":
    test_resume_extraction()

