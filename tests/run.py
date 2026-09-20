"""Unified HireFlow Test Harness Runner.

Command: python -m tests.run
Executes tests 1-10 and prints a comprehensive PASS/FAIL table.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import time

from tests.test_verifier import test_fake_quote_downgraded
from tests.test_determinism import test_determinism_three_runs
from tests.test_golden_set import test_golden_set_accuracy
from tests.test_hero_loop import test_hero_flow
from tests.test_non_answer import test_non_answer_preservation
from tests.test_injection import test_prompt_injection_safety
from tests.test_anonymization import test_pii_and_college_stripped
from tests.test_forbidden_language import test_forbidden_language_in_codebase
from tests.test_edge_cases import (
    test_empty_resume_handling, test_empty_notes_handling,
    test_empty_jd_handling, test_consistency_flags
)
from tests.test_bias_safe import test_bias_safe_masking


def run_all_tests():
    print("\n" + "=" * 80)
    print(" HIREFLOW TEST HARNESS (10/10 EVALUATION SUITE)")
    print("=" * 80)

    tests = [
        ("1. Fake-Quote Verification (Reject invented quote -> Unclear)", test_fake_quote_downgraded),
        ("2. Determinism (3 identical runs on same candidate)", test_determinism_three_runs),
        ("3. Golden Set Accuracy (6 candidates vs expected.json >= 90%)", test_golden_set_accuracy),
        ("4. Hero Flow (C2 Docker Partial -> Clear with history & audit)", test_hero_flow),
        ("5. Non-Answer Handling (Irrelevant answer preserves status & adds gap)", test_non_answer_preservation),
        ("6. Prompt Injection Safety (Adversarial override ignored)", test_prompt_injection_safety),
        ("7. Anonymization & Bias-Safe (PII and colleges stripped)", test_pii_and_college_stripped),
        ("8. Forbidden Language (Zero hire/reject/score terms)", test_forbidden_language_in_codebase),
        ("9. Edge Cases & Degradation (Empty resume/notes/JD graceful)", lambda: (
            test_empty_resume_handling() and
            test_empty_notes_handling() and
            test_empty_jd_handling() and
            test_consistency_flags()
        )),
        ("10. Bias-Safe Masking (Masks names and colleges across screens)", test_bias_safe_masking),
    ]

    results = []
    all_passed = True

    for name, test_fn in tests:
        start_t = time.time()
        try:
            val = test_fn()
            elapsed = (time.time() - start_t) * 1000.0
            if isinstance(val, (int, float)) and val > 1.0:
                detail = f"{val:.1f}% match"
            else:
                detail = f"{elapsed:.1f} ms"
            results.append((name, "PASS", detail))
        except Exception as e:
            elapsed = (time.time() - start_t) * 1000.0
            results.append((name, "FAIL", str(e)[:35]))
            all_passed = False

    print("\n{:<65} {:<10} {:<15}".format("TEST NAME", "RESULT", "METRIC/LATENCY"))
    print("-" * 90)
    for name, status, detail in results:
        print(f"{name:<65} {status:<10} {detail:<15}")

    print("-" * 90)
    summary_text = "ALL 10 TESTS PASSED (10/10)" if all_passed else "SOME TESTS FAILED"
    print(f"OVERALL VERDICT: {summary_text}\n" + "=" * 80 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
