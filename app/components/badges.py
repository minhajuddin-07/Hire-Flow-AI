"""UI Status Badges and Styling Helpers (Vercel Design System).

Signature Vercel aesthetic:
- Minimalist dark surfaces (#0a0a0a, #111111)
- Micro-glowing dot indicators
- Subtle borders (#222222, #333333)
- Crisp typography & monospace code tags
"""

STATUS_STYLES = {
    "Clear": {
        "bg": "rgba(16, 185, 129, 0.08)",
        "text": "#34d399",
        "border": "rgba(16, 185, 129, 0.25)",
        "dot": "#10b981",
        "icon": "●"
    },
    "Partial": {
        "bg": "rgba(59, 130, 246, 0.08)",
        "text": "#60a5fa",
        "border": "rgba(59, 130, 246, 0.25)",
        "dot": "#3b82f6",
        "icon": "●"
    },
    "Unclear": {
        "bg": "rgba(245, 158, 11, 0.08)",
        "text": "#fbbf24",
        "border": "rgba(245, 158, 11, 0.25)",
        "dot": "#f59e0b",
        "icon": "●"
    },
    "Missing": {
        "bg": "rgba(115, 115, 115, 0.08)",
        "text": "#a3a3a3",
        "border": "rgba(115, 115, 115, 0.2)",
        "dot": "#737373",
        "icon": "○"
    }
}


def render_status_badge(status: str) -> str:
    """Returns HTML for an ultra-sleek Vercel-style status pill with glowing dot."""
    cfg = STATUS_STYLES.get(status, STATUS_STYLES["Missing"])
    return (
        f"<span style='display:inline-flex; align-items:center; gap:6px; "
        f"padding:3px 10px; border-radius:9999px; font-size:11px; font-weight:500; "
        f"font-family:ui-monospace, SFMono-Regular, monospace; letter-spacing:0.02em; "
        f"background-color:{cfg['bg']}; color:{cfg['text']}; border:1px solid {cfg['border']};'>"
        f"<span style='font-size:8px; color:{cfg['dot']};'>{cfg['icon']}</span> {status}</span>"
    )


def render_source_badge(source: str) -> str:
    """Returns HTML for source badge (resume vs interview)."""
    if source == "interview":
        return (
            "<span style='display:inline-flex; align-items:center; gap:4px; "
            "padding:2px 8px; border-radius:4px; font-size:10px; font-weight:600; "
            "font-family:ui-monospace, monospace; text-transform:uppercase; letter-spacing:0.05em; "
            "background-color:rgba(168, 85, 247, 0.1); color:#c084fc; border:1px solid rgba(168, 85, 247, 0.3);'>"
            "INTERVIEW</span>"
        )
    return (
        "<span style='display:inline-flex; align-items:center; gap:4px; "
        "padding:2px 8px; border-radius:4px; font-size:10px; font-weight:600; "
        "font-family:ui-monospace, monospace; text-transform:uppercase; letter-spacing:0.05em; "
        "background-color:#141414; color:#737373; border:1px solid #262626;'>"
        "RESUME</span>"
    )


def render_priority_badge(priority: str) -> str:
    """Returns HTML for must_have vs nice_to_have."""
    if priority == "must_have":
        return (
            "<span style='padding:2px 6px; border-radius:4px; font-size:9px; font-weight:700; "
            "font-family:ui-monospace, monospace; text-transform:uppercase; letter-spacing:0.06em; "
            "background-color:rgba(239, 68, 68, 0.1); color:#f87171; border:1px solid rgba(239, 68, 68, 0.3);'>"
            "Must Have</span>"
        )
    return (
        "<span style='padding:2px 6px; border-radius:4px; font-size:9px; font-weight:600; "
        "font-family:ui-monospace, monospace; text-transform:uppercase; letter-spacing:0.06em; "
        "background-color:#171717; color:#a3a3a3; border:1px solid #2e2e2e;'>"
        "Nice to Have</span>"
    )


def render_flag_badge(flag_type: str, text: str) -> str:
    """Returns HTML for consistency flag alert in Vercel minimalist style."""
    return (
        f"<div style='margin-bottom:8px; padding:10px 14px; border-radius:8px; "
        f"background-color:rgba(245, 158, 11, 0.05); border:1px solid rgba(245, 158, 11, 0.25); "
        f"color:#fef3c7; font-size:12px; display:flex; align-items:center; gap:8px;'>"
        f"<span style='color:#f59e0b; font-size:14px;'>▲</span> "
        f"<span><strong>Worth Clarifying:</strong> {text}</span></div>"
    )
