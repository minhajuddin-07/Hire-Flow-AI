"""Fairness and Bias-Safe Anonymizer.

Rule R6: Strip name, gender, age, photo references, contact info, and college
names from text BEFORE it is sent to the LLM for mapping. Names are re-attached
in the UI only. Bias-Safe toggle masks them on screen too.
"""

import re
from typing import Tuple, List, Dict

# Known college/university pattern identifiers
COLLEGE_PATTERNS = [
    r"\b(?:University|College|Institute|Polytechnic|Academy|School of)\s+of\s+[A-Za-z\s]+",
    r"\b[A-Za-z\s]+(?:\s+(?:University|College|Institute|Polytechnic|Academy))\b",
    r"\b(?:Harvard|MIT|Stanford|Berkeley|Carnegie Mellon|Oxford|Cambridge|Princeton|Yale|Columbia|Cornell|Caltech|Georgia Tech)\b",
    r"\b(?:State University|City College|National Institute|Metro Tech Institute)\b"
]

GENDER_AGE_PATTERNS = [
    (r"\b(he|she|him|her|his|hers|himself|herself)\b", "[they/them]"),
    (r"\b(?:male|female|man|woman|gentleman|lady)\b", "[individual]"),
    (r"\b(?:age[:\s]+\d{2}|\b\d{2}\s*years\s*old)\b", "[AGE MASKED]"),
    (r"\b(?:born\s+in\s+\d{4}|dob[:\s]+\d{2}[/-]\d{2}[/-]\d{2,4})\b", "[DOB MASKED]"),
    (r"\b(?:photo|headshot|picture|profile image)\b", "[IMAGE REMOVED]")
]

CONTACT_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "[EMAIL MASKED]"),
    (r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE MASKED]"),
    (r"\b(?:linkedin\.com/in/[a-zA-Z0-9_-]+|github\.com/[a-zA-Z0-9_-]+)\b", "[URL MASKED]")
]


def anonymize_text(raw_text: str, candidate_name: str = "") -> Tuple[str, Dict[str, str]]:
    """Strips candidate name, college/university, contact info, gender, and age

    indicators from raw resume text before sending to LLM.
    Returns:
        (anonymized_text, metadata_dict)
    """
    text = raw_text

    # 1. Mask candidate name if provided or detectable at top
    if candidate_name and candidate_name.strip():
        name_parts = candidate_name.strip().split()
        for part in name_parts:
            if len(part) > 2:
                text = re.sub(rf"\b{re.escape(part)}\b", "[CANDIDATE]", text, flags=re.IGNORECASE)

    # 2. Mask Contact info
    for pattern, replacement in CONTACT_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # 3. Mask Colleges and Universities
    for col_pattern in COLLEGE_PATTERNS:
        text = re.sub(col_pattern, "[ACADEMIC INSTITUTION]", text, flags=re.IGNORECASE)

    # 4. Mask Gender and Age indicators
    for gen_pattern, replacement in GENDER_AGE_PATTERNS:
        text = re.sub(gen_pattern, replacement, text, flags=re.IGNORECASE)

    # 5. Mask first line name header heuristic if still present
    lines = text.strip().split("\n")
    if lines:
        first_line = lines[0].strip()
        if len(first_line.split()) in [2, 3] and not any(w in first_line.lower() for w in ["resume", "curriculum", "engineer", "developer"]):
            lines[0] = "[CANDIDATE NAME MASKED]"
            text = "\n".join(lines)

    return text, {"status": "anonymized"}


def mask_for_bias_safe_display(candidate_name: str, anon_label: str, enabled: bool) -> str:
    """Returns candidate name or bias-safe anonymous label based on toggle."""
    if enabled:
        return anon_label
    return candidate_name
