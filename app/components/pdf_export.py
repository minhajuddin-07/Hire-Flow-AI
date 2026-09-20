"""PDF Report Generator for HireFlow.

Uses ReportLab to generate recruiter-grade, auditable candidate evidence reports
without hire/reject verdicts or numeric scores.
"""

import io
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from engine.schema import Candidate, Role


def generate_candidate_pdf(candidate: Candidate, role: Role, bias_safe: bool = False) -> bytes:
    """Generates a professional PDF evidence report as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b")
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#64748b")
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155")
    )
    quote_style = ParagraphStyle(
        "QuoteText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0284c7")
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#94a3b8")
    )

    story = []

    # Title & Candidate Header
    cand_display_name = candidate.anon_label if bias_safe else candidate.name
    story.append(Paragraph("HireFlow Evidence & Verification Report", title_style))
    story.append(Paragraph(f"Candidate: <b>{cand_display_name}</b> | Role: <b>{role.title}</b>", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1")))
    story.append(Spacer(1, 10))

    # Candidate Summary
    story.append(Paragraph("Candidate Summary", section_style))
    story.append(Paragraph(candidate.summary or "No summary provided.", body_style))
    story.append(Spacer(1, 8))

    # Requirement Verification Breakdown Table
    story.append(Paragraph("Requirement Verification Breakdown", section_style))

    table_data = [
        [
            Paragraph("<b>Req ID</b>", body_style),
            Paragraph("<b>Requirement</b>", body_style),
            Paragraph("<b>Status</b>", body_style),
            Paragraph("<b>Source</b>", body_style),
            Paragraph("<b>Verified Quote & Reasoning</b>", body_style)
        ]
    ]

    req_map = {r.id: r for r in role.requirements}

    for m in candidate.mappings:
        req_text = req_map.get(m.requirement_id).text if m.requirement_id in req_map else m.requirement_id
        quote_text = f'"{m.evidence}"' if m.evidence else "<i>(None)</i>"
        detail_text = f"{quote_text}<br/><font color='#64748b' size='8'>{m.reasoning}</font>"

        status_color = colors.HexColor("#10b981") if m.status == "Clear" else (
            colors.HexColor("#3b82f6") if m.status == "Partial" else (
                colors.HexColor("#f59e0b") if m.status == "Unclear" else colors.HexColor("#6b7280")
            )
        )

        table_data.append([
            Paragraph(m.requirement_id, body_style),
            Paragraph(req_text, body_style),
            Paragraph(f"<b>{m.status}</b>", ParagraphStyle("Status", parent=body_style, textColor=status_color)),
            Paragraph(m.source.capitalize(), body_style),
            Paragraph(detail_text, body_style)
        ])

    breakdown_table = Table(table_data, colWidths=[45, 130, 60, 55, 240])
    breakdown_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(breakdown_table)
    story.append(Spacer(1, 14))

    # Interview Status Transitions (if any)
    has_history = any(len(m.history) > 0 for m in candidate.mappings)
    if has_history:
        story.append(Paragraph("Interview Evidence Transitions", section_style))
        for m in candidate.mappings:
            for ch in m.history:
                trans_text = (
                    f"• <b>{m.requirement_id}</b>: Status transitioned from <b>{ch.from_status}</b> "
                    f"to <b>{ch.to_status}</b> based on interview answer.<br/>"
                    f"&nbsp;&nbsp;<i>Verbatim quote:</i> \"{ch.evidence}\"<br/>"
                    f"&nbsp;&nbsp;<i>Reason:</i> {ch.reason}"
                )
                story.append(Paragraph(trans_text, body_style))
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 10))

    # Consistency Flags & Focus Areas
    if candidate.flags:
        story.append(Paragraph("Consistency Observations (Worth Clarifying)", section_style))
        for flg in candidate.flags:
            story.append(Paragraph(f"⚠️ {flg.description}", body_style))
        story.append(Spacer(1, 10))

    # Human Recruiter Sign-Off & Copilot Disclaimer
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Human Recruiter Sign-Off & Notes", section_style))
    story.append(Paragraph("Notes: __________________________________________________________________________", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Decision Maker Signature: ___________________________ Date: ____________________", body_style))
    story.append(Spacer(1, 14))

    disclaimer = (
        "<b>Notice:</b> HireFlow is an evidence-driven copilot. It does not output automated hire/reject "
        "decisions or numeric ranking scores. The AI surfaces verified evidence; humans make the hiring decision."
    )
    story.append(Paragraph(disclaimer, disclaimer_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
