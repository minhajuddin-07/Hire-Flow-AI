"""Test 10: Bias-Safe Mode Verification Test.

Rule R6: Bias-Safe toggle hides names/colleges in every screen.
"""

from engine.anonymizer import mask_for_bias_safe_display, anonymize_text


def test_bias_safe_masking():
    cand_name = "Alex Rivera"
    anon_label = "Candidate 2"

    # 1. When Bias-Safe is OFF
    display_off = mask_for_bias_safe_display(cand_name, anon_label, enabled=False)
    assert display_off == cand_name, f"Expected {cand_name}, got {display_off}"

    # 2. When Bias-Safe is ON
    display_on = mask_for_bias_safe_display(cand_name, anon_label, enabled=True)
    assert display_on == anon_label, f"Expected {anon_label}, got {display_on}"
    assert "Alex" not in display_on
    assert "Rivera" not in display_on

    # 3. Source text masking check
    sample_text = "Graduated from Stanford University with honors. Alex Rivera joined Acme Corp."
    masked, _ = anonymize_text(sample_text, candidate_name="Alex Rivera")
    assert "Stanford University" not in masked
    assert "Alex Rivera" not in masked
    assert "[ACADEMIC INSTITUTION]" in masked or "[CANDIDATE]" in masked

    return True


if __name__ == "__main__":
    test_bias_safe_masking()
    print("PASS: test_bias_safe_masking")
