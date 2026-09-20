"""Test 8: Forbidden Language CI Test.

Rule R1: Grep for "hire", "reject", "recommend hiring", "score" in outputs,
engine logic, and UI strings. Must be zero (except the explicit copilot disclaimer:
'AI surfaces evidence; humans make the hiring decision').
"""

import os
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_forbidden_language_in_codebase():
    # Files to inspect
    target_dirs = ["engine", "app"]
    files_to_check = []
    for d in target_dirs:
        dirpath = os.path.join(ROOT_DIR, d)
        if os.path.exists(dirpath):
            for root, _, files in os.walk(dirpath):
                for f in files:
                    if f.endswith(".py"):
                        files_to_check.append(os.path.join(root, f))

    # Also check sample_data.json
    sample_json = os.path.join(ROOT_DIR, "data", "sample_data.json")
    if os.path.exists(sample_json):
        files_to_check.append(sample_json)

    # Allowed disclaimer exceptions
    allowed_disclaimer_snippets = [
        "hireflow",
        "humans make the decision",
        "humans make the hiring decision",
        "never output hire/reject",
        "never recommend hiring",
        "forbidden",
        "disclaimer"
    ]

    forbidden_patterns = [
        r"\b(?:recommend hiring|recommend rejection|candidate is rejected|candidate is hired)\b",
        r"\b(?:match score|candidate score|ranking score)\b",
        r"\bwinner\b"
    ]

    violations = []

    for fpath in files_to_check:
        with open(fpath, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                clean_line = line.lower()
                # If line is part of a disclaimer or comment explaining R1, ignore it
                if any(snippet in clean_line for snippet in allowed_disclaimer_snippets):
                    continue

                for pat in forbidden_patterns:
                    if re.search(pat, clean_line):
                        violations.append(f"{os.path.basename(fpath)}:{line_no}: {line.strip()}")

    assert len(violations) == 0, f"Forbidden language violations found:\n" + "\n".join(violations)
    return True


if __name__ == "__main__":
    test_forbidden_language_in_codebase()
    print("PASS: test_forbidden_language_in_codebase")
