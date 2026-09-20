"""UI Status Badges and Styling Helpers.

Rule R7: Statuses: Clear | Partial | Unclear | Missing only.
Consistent status colors:
- Missing: Gray
- Unclear: Amber
- Partial: Blue
- Clear: Green
"""

import streamlit as st


STATUS_STYLES = {
    "Clear": {
        "bg": "#064e3b",
        "text": "#6ee7b7",
        "border": "#059669",
        "icon": "✓"
    },
    "Partial": {
        "bg": "#1e3a8a",
        "text": "#93c5fd",
        "border": "#2563eb",
        "icon": "◐"
    },
    "Unclear": {
        "bg": "#78350f",
        "text": "#fde68a",
        "border": "#d97706",
        "icon": "?"
    },
    "Missing": {
        "bg": "#374151",
        "text": "#d1d5db",
        "border": "#4b5563",
        "icon": "✕"
    }
}


def render_status_badge(status: str) -> str:
    """Returns HTML for inline status badge."""
    cfg = STATUS_STYLES.get(status, STATUS_STYLES["Missing"])
    return (
        f"<span style='display:inline-flex; align-items:center; gap:4px; "
        f"padding:2px 8px; border-radius:12px; font-size:12px; font-weight:600; "
        f"background-color:{cfg['bg']}; color:{cfg['text']}; border:1px solid {cfg['border']};'>"
        f"{cfg['icon']} {status}</span>"
    )


def render_source_badge(source: str) -> str:
    """Returns HTML for source badge (resume vs interview)."""
    if source == "interview":
        return (
            "<span style='display:inline-flex; align-items:center; gap:4px; "
            "padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600; "
            "background-color:#581c87; color:#d8b4fe; border:1px solid #7e22ce;'>"
            "🎤 Interview</span>"
        )
    return (
        "<span style='display:inline-flex; align-items:center; gap:4px; "
        "padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600; "
        "background-color:#1f2937; color:#9ca3af; border:1px solid #374151;'>"
        "📄 Resume</span>"
    )


def render_priority_badge(priority: str) -> str:
    """Returns HTML for must_have vs nice_to_have."""
    if priority == "must_have":
        return (
            "<span style='padding:2px 6px; border-radius:6px; font-size:10px; font-weight:700; "
            "background-color:#450a0a; color:#fca5a5; border:1px solid #991b1b; text-transform:uppercase;'>"
            "Must Have</span>"
        )
    return (
        "<span style='padding:2px 6px; border-radius:6px; font-size:10px; font-weight:600; "
        "background-color:#1e1b4b; color:#c7d2fe; border:1px solid #3730a3; text-transform:uppercase;'>"
        "Nice to Have</span>"
    )


def render_flag_badge(flag_type: str, text: str) -> str:
    """Returns HTML for consistency flag alert."""
    return (
        f"<div style='margin-bottom:8px; padding:8px 12px; border-radius:6px; "
        f"background-color:#451a03; border-left:4px solid #f59e0b; color:#fef3c7; font-size:13px;'>"
        f"⚠️ <strong>Worth Clarifying:</strong> {text}</div>"
    )
