import json
import os
from pathlib import Path
from typing import Any, List
from models import AuditEntry

AUDIT_FILE = Path(__file__).parent / "data" / "audit.json"


def log_entry(
    insight_id: str,
    step: str,
    inputs_used: List[Any],
    prompt_version: str,
    output: Any,
) -> AuditEntry:
    """Log an AI decision or extraction to the persistent audit file."""
    entry = AuditEntry(
        insight_id=insight_id,
        step=step,
        inputs_used=inputs_used,
        prompt_version=prompt_version,
        output=output,
    )

    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    records = []
    if AUDIT_FILE.exists():
        try:
            with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    records = json.loads(content)
        except Exception:
            records = []

    records.append(entry.model_dump())

    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    return entry


def get_audit_trail() -> List[dict]:
    """Retrieve all audit entries."""
    if not AUDIT_FILE.exists():
        return []
    try:
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except Exception:
        return []


def clear_audit_trail() -> None:
    """Clear all records from audit file."""
    if AUDIT_FILE.exists():
        with open(AUDIT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

