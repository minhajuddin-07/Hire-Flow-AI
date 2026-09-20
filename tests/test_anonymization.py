"""Test 7: Anonymization & PII Stripping Test.

Rule R6: LLM input contains no candidate name, email, phone, or college names.
"""

from engine.anonymizer import anonymize_text


def test_pii_and_college_stripped():
    sample_raw = (
        "Sarah Chen\n"
        "Email: sarah.chen@example.com | Phone: 555-321-9876\n"
        "Graduated from State University with a B.S. in Computer Science.\n"
        "She led microservice engineering across distributed teams."
    )

    anonymized, _ = anonymize_text(sample_raw, candidate_name="Sarah Chen")

    # Verify candidate name stripped
    assert "sarah" not in anonymized.lower(), "Candidate first name not stripped"
    assert "chen" not in anonymized.lower(), "Candidate last name not stripped"

    # Verify contact info stripped
    assert "sarah.chen@example.com" not in anonymized, "Email not stripped"
    assert "555-321-9876" not in anonymized, "Phone not stripped"

    # Verify College stripped
    assert "State University" not in anonymized, "College name not stripped"

    # Verify gender pronoun masked
    assert " she " not in f" {anonymized.lower()} ", "Gender pronoun not masked"

    return True


if __name__ == "__main__":
    test_pii_and_college_stripped()
    print("PASS: test_pii_and_college_stripped")
