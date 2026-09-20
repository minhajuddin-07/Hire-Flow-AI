"""Verbatim Quote Verifier.

Rule R3: Every status carries a verbatim quote. CODE verifies the quote exists
in the source (normalize whitespace/case/punctuation). If not: evidence=null,
status="Unclear", log "quote could not be verified". Never invent evidence.
Supports standard resumes and multi-column layout de-wrapping.
"""

import re
from typing import Tuple, Optional


def normalize_text(text: str) -> str:
    """Normalize text by collapsing whitespace, newlines, and lowering case."""
    if not text:
        return ""
    # Normalize unicode quotes and dashes
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    text = text.replace("—", "-").replace("–", "-")
    # Collapse all whitespace and newlines to single spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def decolumnize_text(text: str) -> str:
    """De-wraps multi-column text formats (e.g. resumes formatted with '|' or tabs)."""
    if not text or "|" not in text:
        return text
    left_col, right_col = [], []
    for line in text.splitlines():
        if "|" in line:
            parts = line.split("|", 1)
            left_col.append(parts[0].strip())
            right_col.append(parts[1].strip())
        else:
            left_col.append(line.strip())
    return " ".join(left_col) + " " + " ".join(right_col)


def verify_quote(source_text: str, quote: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """Verifies that the provided quote exists verbatim in source_text.

    Returns:
        (is_verified, verified_quote_or_none, log_message)
    """
    if not quote or not quote.strip():
        return False, None, "No quote provided"

    if not source_text or not source_text.strip():
        return False, None, "Source text is empty"

    norm_source = normalize_text(source_text)
    norm_quote = normalize_text(quote)

    if not norm_quote:
        return False, None, "Quote was empty after normalization"

    # 1. Direct substring search
    if norm_quote in norm_source:
        return True, quote.strip(), "Quote verified successfully"

    # 2. Check with punctuation stripped
    clean_source = re.sub(r"[^\w\s]", "", norm_source)
    clean_quote = re.sub(r"[^\w\s]", "", norm_quote)

    if clean_quote and clean_quote in clean_source:
        return True, quote.strip(), "Quote verified (normalized punctuation)"

    # 3. Check against de-columnized source text (for multi-column resumes)
    if "|" in source_text:
        decol_source = normalize_text(decolumnize_text(source_text))
        if norm_quote in decol_source:
            return True, quote.strip(), "Quote verified (de-columnized layout)"
        clean_decol = re.sub(r"[^\w\s]", "", decol_source)
        if clean_quote and clean_quote in clean_decol:
            return True, quote.strip(), "Quote verified (de-columnized normalized layout)"

    # Quote could not be verified in source
    return False, None, "quote could not be verified in source text"
