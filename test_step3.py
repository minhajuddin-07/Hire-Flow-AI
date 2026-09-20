import os
from pathlib import Path
from pipeline import extract_requirements, evaluate_resume_requirements, validate_quote
from audit import get_audit_trail
from models import Requirement, RequirementRecord

def test_step3_evaluation():
    samples_dir = Path(__file__).parent / "data" / "samples"
    jd_path = samples_dir / "job_description.txt"
    resume_strong_path = samples_dir / "resume_strong_vague.txt"
    resume_partial_path = samples_dir / "resume_partial_fit.txt"

    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    with open(resume_strong_path, "r", encoding="utf-8") as f:
        resume_strong_text = f.read()

    with open(resume_partial_path, "r", encoding="utf-8") as f:
        resume_partial_text = f.read()

    print("\n--- STEP 1: Extracting Requirements from JD ---")
    reqs = extract_requirements(jd_text)
    assert len(reqs) >= 5, "Should extract at least 5 requirements"
    print(f"Extracted {len(reqs)} requirements.")

    # -------------------------------------------------------------
    # Test 1: Strong-but-vague resume evaluation
    # -------------------------------------------------------------
    print("\n--- STEP 3 (TEST 1): Evaluating Strong-but-Vague Resume ---")
    records_strong = evaluate_resume_requirements(reqs, resume_strong_text)
    assert len(records_strong) == len(reqs), "Must create exactly one RequirementRecord per requirement"

    statuses_strong = [r.status for r in records_strong]
    print(f"Strong/Vague Resume Statuses: {statuses_strong}")
    for rec in records_strong:
        quotes_str = " | ".join([f'"{e.quote}"' for e in rec.evidence]) or "No Quote"
        print(f"[{rec.requirement_id}] Status: {rec.status.upper():<7} | Conf: {rec.confidence:<6} | Evidence: {quotes_str}")

    # CHECK: strong-but-vague resume shows a mix of met/partial/unclear, NOT all met
    met_count = sum(1 for s in statuses_strong if s == "met")
    partial_count = sum(1 for s in statuses_strong if s == "partial")
    unclear_count = sum(1 for s in statuses_strong if s == "unclear")
    missing_count = sum(1 for s in statuses_strong if s == "missing")

    print(f"\nBreakdown -> Met: {met_count}, Partial: {partial_count}, Unclear: {unclear_count}, Missing: {missing_count}")

    assert met_count > 0, "Strong/vague resume should have at least some 'met' criteria"
    assert (partial_count > 0 or unclear_count > 0), "Strong/vague resume must show 'partial' or 'unclear' due to vague claims"
    assert met_count < len(records_strong), "CHECK CRITICAL: Strong-but-vague resume MUST NOT be marked all 'met'!"

    # Hard Rule 1 Quote Check for Strong Resume
    for rec in records_strong:
        for ev in rec.evidence:
            assert ev.quote in resume_strong_text, f"Hard Rule 1 violation: Quote '{ev.quote}' not found verbatim in strong resume text!"

    print("[CHECK PASSED] Strong-but-vague resume correctly evaluated to a calibrated mix of met/partial/unclear!")

    # -------------------------------------------------------------
    # Test 2: Partial-fit resume evaluation
    # -------------------------------------------------------------
    print("\n--- STEP 3 (TEST 2): Evaluating Partial-Fit Resume ---")
    records_partial = evaluate_resume_requirements(reqs, resume_partial_text)
    assert len(records_partial) == len(reqs)

    statuses_partial = [r.status for r in records_partial]
    print(f"Partial Fit Resume Statuses: {statuses_partial}")
    for rec in records_partial:
        quotes_str = " | ".join([f'"{e.quote}"' for e in rec.evidence]) or "No Quote"
        print(f"[{rec.requirement_id}] Status: {rec.status.upper():<7} | Conf: {rec.confidence:<6} | Evidence: {quotes_str}")

    # Verify partial-fit has partial, unclear, and missing
    assert "partial" in statuses_partial, "Partial resume should have 'partial' status items"
    assert ("missing" in statuses_partial or "unclear" in statuses_partial), "Partial resume should have 'missing' or 'unclear' items"

    # Hard Rule 1 Quote Check for Partial Resume
    for rec in records_partial:
        for ev in rec.evidence:
            assert ev.quote in resume_partial_text, f"Hard Rule 1 violation: Quote '{ev.quote}' not found verbatim in partial resume text!"

    print("[CHECK PASSED] Partial-fit resume correctly evaluated and 100% verbatim grounded!")

    # -------------------------------------------------------------
    # Test 3: Audit Trail Verification
    # -------------------------------------------------------------
    trail = get_audit_trail()
    assert len(trail) > 0
    step3_entries = [entry for entry in trail if entry.get("step") == "map_resume_requirements"]
    assert len(step3_entries) >= 2, "Audit trail must log every Step 3 mapping execution"

    print("\nALL STEP 3 PIPELINE & CHECK VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_step3_evaluation()
