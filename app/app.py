"""HireFlow: Evidence-Driven Interview Copilot.

Five Screens:
1. Role Setup (Editable Requirements)
2. Candidate Pool (Buckets, Status Counts, Filters, Cited Recruiter Chat)
3. Candidate Detail (Summary, Evidence Map, Verified Quotes, Flags, Audit Trail)
4. Interview Room (Live Notes, 1-Click Hero Answer, Before/After Diff, Coverage)
5. Compare & Report (Side-by-Side Candidate Matrix, Focus Areas, PDF Export)
"""

import os
import sys

# Ensure root directory is in sys.path regardless of execution cwd or nested script path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import json
import time
import streamlit as st

from engine.schema import (
    Requirement, Role, Candidate, CandidateMapping, StatusChange,
    ConsistencyFlag, AuditEntry
)
from engine.llm import extract_requirements, map_candidate, analyze_answer, ask_pool
from engine.anonymizer import mask_for_bias_safe_display
try:
    from components.badges import (
        render_status_badge, render_source_badge, render_priority_badge,
        render_flag_badge, STATUS_STYLES
    )
    from components.pdf_export import generate_candidate_pdf
except ImportError:
    from app.components.badges import (
        render_status_badge, render_source_badge, render_priority_badge,
        render_flag_badge, STATUS_STYLES
    )
    from app.components.pdf_export import generate_candidate_pdf

# Set page config
st.set_page_config(
    page_title="HireFlow | Evidence-Driven Interview Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Authentic Vercel Geek Aesthetic)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');

    /* Vercel Root Dark Theme */
    .stApp {
        background-color: #000000;
        color: #ededed;
        font-family: 'Geist', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        letter-spacing: -0.01em;
    }
    
    /* Vercel Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
        font-family: 'Geist', sans-serif;
        font-weight: 600;
        letter-spacing: -0.025em;
    }
    
    /* Vercel Minimal Card */
    .metric-card {
        background-color: #0a0a0a;
        border: 1px solid #1f1f1f;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 14px;
        transition: border-color 0.15s ease, transform 0.15s ease;
    }
    .metric-card:hover {
        border-color: #333333;
    }
    
    /* Vercel Monospace Evidence Box */
    .evidence-box {
        background-color: #0c0c0c;
        border: 1px solid #222222;
        border-left: 3px solid #ededed;
        border-radius: 6px;
        padding: 12px 14px;
        margin: 8px 0;
        font-size: 13px;
    }
    
    .quote-text {
        font-family: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
        color: #e5e5e5;
        font-size: 12px;
        background-color: #141414;
        border: 1px solid #262626;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
        margin: 4px 0;
        line-height: 1.5;
    }
    
    /* Vercel Status Change Feed Card */
    .status-feed-card {
        background-color: #0a0a0a;
        border: 1px solid #1f1f1f;
        border-left: 3px solid #10b981;
        border-radius: 8px;
        padding: 16px;
        margin-top: 12px;
    }

    /* Vercel Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #050505;
        border-right: 1px solid #1a1a1a;
    }

    /* Buttons */
    button[kind="primary"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        border: none !important;
        transition: opacity 0.15s ease !important;
    }
    button[kind="primary"]:hover {
        opacity: 0.9 !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #ffffff;
    }

    /* Copilot Minimal Disclaimer */
    .copilot-disclaimer {
        font-family: 'Geist Mono', monospace;
        font-size: 10px;
        color: #737373;
        border-top: 1px solid #1a1a1a;
        padding-top: 14px;
        margin-top: 24px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Session State Initialization
# ----------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SAMPLE_PATH = os.path.join(DATA_DIR, "sample_data.json")
DEMO_DIR = os.path.join(DATA_DIR, "demo")


def load_initial_data():
    """Loads candidate pool and role from sample_data.json or demo files."""
    if os.path.exists(SAMPLE_PATH):
        with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        role = Role.model_validate(data["role"])
        candidates = [Candidate.model_validate(c) for c in data["candidates"]]
        return role, candidates

    # Fallback to demo files
    with open(os.path.join(DEMO_DIR, "jd.txt"), "r", encoding="utf-8") as f:
        jd_text = f.read()
    role = extract_requirements(jd_text)
    return role, []


if "role" not in st.session_state or "candidates" not in st.session_state:
    role_init, cands_init = load_initial_data()
    st.session_state.role = role_init
    st.session_state.candidates = cands_init
    st.session_state.selected_candidate_id = cands_init[0].id if cands_init else None
    st.session_state.chat_history = []


# ----------------------------------------------------------------------
# Sidebar Controls & Global Toggles
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚡ HireFlow")
    st.caption("Evidence-Driven Interview Copilot")
    st.markdown("---")

    # Demo Mode Toggle
    demo_mode = st.toggle("⚡ Demo Mode (Offline)", value=True, help="Bypasses live LLM calls, uses pre-seeded disk cache")
    # Bias-Safe Mode Toggle (Rule R6)
    bias_safe = st.toggle("🛡️ Bias-Safe Mode", value=False, help="Masks candidate names and colleges across all views")

    st.markdown("---")
    st.markdown("### Navigation")
    active_screen = st.radio(
        "Workflow Stage",
        [
            "1. Role Setup",
            "2. Candidate Pool",
            "3. Candidate Detail",
            "4. Interview Room",
            "5. Compare & Report"
        ],
        index=1
    )

    st.markdown("---")
    # Candidate Quick Selector
    cand_options = {
        c.id: mask_for_bias_safe_display(c.name, c.anon_label, bias_safe)
        for c in st.session_state.candidates
    }
    if cand_options:
        sel_cid = st.selectbox(
            "Active Candidate",
            options=list(cand_options.keys()),
            format_func=lambda cid: cand_options[cid],
            index=1 if len(cand_options) > 1 else 0
        )
        st.session_state.selected_candidate_id = sel_cid

    # Load Last Run button
    if st.button("🔄 Reset / Load Golden Demo Run", use_container_width=True):
        role_r, cands_r = load_initial_data()
        st.session_state.role = role_r
        st.session_state.candidates = cands_r
        st.success("Loaded golden run state!")
        st.rerun()

    # Rule R1 Copilot Disclaimer
    st.markdown(
        "<div class='copilot-disclaimer'>"
        "<strong>Notice:</strong> HireFlow is an evidence copilot, not a resume screener. "
        "The AI surfaces verifiable evidence; humans make the hiring decision. "
        "No automated hire/reject decisions or match percentages are produced."
        "</div>",
        unsafe_allow_html=True
    )


# Helper: Get Active Candidate
active_candidate = next(
    (c for c in st.session_state.candidates if c.id == st.session_state.selected_candidate_id),
    st.session_state.candidates[0] if st.session_state.candidates else None
)


# Helper: Qualitative Bucketing Logic (Rule R1)
def compute_bucket(cand: Candidate, role: Role) -> tuple[str, str]:
    """Categorizes candidate into qualitative fit buckets based purely on clear counts."""
    clear_count = sum(1 for m in cand.mappings if m.status == "Clear")
    must_have_ids = {r.id for r in role.requirements if r.priority == "must_have"}
    must_have_clears = sum(1 for m in cand.mappings if m.requirement_id in must_have_ids and m.status == "Clear")

    if clear_count >= 6 and must_have_clears >= 4:
        return "Strong Fit", f"{clear_count} of {len(role.requirements)} requirements Clear ({must_have_clears} Must-Haves verified)"
    elif clear_count >= 3:
        return "Partial Fit", f"{clear_count} of {len(role.requirements)} requirements Clear; key technical or cloud areas need validation"
    else:
        return "Needs Validation", f"Only {clear_count} of {len(role.requirements)} requirements Clear; substantial evidence gaps"


# ----------------------------------------------------------------------
# SCREEN 1: Role Setup
# ----------------------------------------------------------------------
if active_screen.startswith("1."):
    st.title("⚙️ Screen 1: Role Setup & Requirement Engineering")
    st.markdown("Extract, edit, and prioritize discrete requirements from the Job Description. The recruiter retains full editing control.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Role Metadata")
        role_title = st.text_input("Role Title", value=st.session_state.role.title)
        st.session_state.role.title = role_title

        jd_default_path = os.path.join(DEMO_DIR, "jd.txt")
        jd_default_text = ""
        if os.path.exists(jd_default_path):
            with open(jd_default_path, "r", encoding="utf-8") as f:
                jd_default_text = f.read()

        jd_input = st.text_area("Job Description Text", value=jd_default_text, height=260)
        if st.button("✨ Re-extract Requirements from JD (Call A)"):
            with st.spinner("Extracting discrete requirements via Call A..."):
                extracted_role = extract_requirements(jd_input)
                st.session_state.role = extracted_role
                st.success(f"Extracted {len(extracted_role.requirements)} discrete criteria!")
                st.rerun()

    with col2:
        st.subheader("Configured Requirements (Recruiter Editable)")
        reqs_to_keep = []
        for i, req in enumerate(st.session_state.role.requirements):
            with st.expander(f"{req.id}: {req.text[:45]}...", expanded=False):
                c_a, c_b = st.columns([3, 1])
                new_text = c_a.text_input(f"Text ({req.id})", value=req.text, key=f"req_txt_{i}")
                new_priority = c_b.selectbox(
                    f"Priority ({req.id})",
                    ["must_have", "nice_to_have"],
                    index=0 if req.priority == "must_have" else 1,
                    key=f"req_prio_{i}"
                )
                new_cat = st.selectbox(
                    f"Category ({req.id})",
                    ["skill", "experience", "education", "leadership"],
                    index=["skill", "experience", "education", "leadership"].index(req.category) if req.category in ["skill", "experience", "education", "leadership"] else 0,
                    key=f"req_cat_{i}"
                )
                if not st.checkbox(f"Delete {req.id}", key=f"del_{i}"):
                    reqs_to_keep.append(Requirement(id=req.id, text=new_text, category=new_cat, priority=new_priority))

        # Add new requirement row
        st.markdown("#### Add New Requirement")
        c_add1, c_add2, c_add3 = st.columns([3, 1, 1])
        new_r_text = c_add1.text_input("New Requirement Text", placeholder="e.g. Experience with Kubernetes")
        new_r_cat = c_add2.selectbox("Category", ["skill", "experience", "education", "leadership"], key="new_cat_sel")
        new_r_prio = c_add3.selectbox("Priority", ["must_have", "nice_to_have"], key="new_prio_sel")

        if st.button("➕ Add Requirement"):
            if new_r_text.strip():
                new_id = f"R{len(reqs_to_keep)+1}"
                reqs_to_keep.append(Requirement(id=new_id, text=new_r_text.strip(), category=new_r_cat, priority=new_r_prio))
                st.session_state.role.requirements = reqs_to_keep
                st.success(f"Added {new_id}!")
                st.rerun()

        st.session_state.role.requirements = reqs_to_keep


# ----------------------------------------------------------------------
# SCREEN 2: Candidate Pool
# ----------------------------------------------------------------------
elif active_screen.startswith("2."):
    st.title("👥 Screen 2: Candidate Pool & Intelligence")
    st.markdown(f"**Role:** {st.session_state.role.title} &nbsp;|&nbsp; **Total Candidates:** {len(st.session_state.candidates)}")

    # Pool Filter Controls
    f_col1, f_col2 = st.columns([2, 2])
    with f_col1:
        bucket_filter = st.multiselect(
            "Filter by Fit Bucket",
            ["Strong Fit", "Partial Fit", "Needs Validation"],
            default=["Strong Fit", "Partial Fit", "Needs Validation"]
        )
    with f_col2:
        flag_filter = st.checkbox("Show Only Candidates with Consistency Flags (Worth Clarifying)", value=False)

    st.markdown("---")

    # Render Candidates Table / Cards
    cols = st.columns(3)
    col_idx = 0

    for cand in st.session_state.candidates:
        bucket, bucket_why = compute_bucket(cand, st.session_state.role)
        if bucket not in bucket_filter:
            continue
        if flag_filter and len(cand.flags) == 0:
            continue

        c_name_disp = mask_for_bias_safe_display(cand.name, cand.anon_label, bias_safe)
        clear_cnt = sum(1 for m in cand.mappings if m.status == "Clear")
        total_reqs = len(st.session_state.role.requirements)

        with cols[col_idx % 3]:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <h3 style='margin:0;'>{c_name_disp}</h3>
                    <span style='font-size:12px; font-weight:700; color:#388bfd;'>{bucket}</span>
                </div>
                <p style='font-size:12px; color:#8b949e; margin:6px 0;'>{cand.summary[:95]}...</p>
                <div style='margin:8px 0; font-size:13px;'>
                    <strong>Coverage:</strong> {clear_cnt} of {total_reqs} Clear
                </div>
            """, unsafe_allow_html=True)

            # Mini status badges row
            badges_html = " ".join([render_status_badge(m.status) for m in cand.mappings[:4]])
            st.markdown(f"<div style='margin-bottom:8px;'>{badges_html}</div>", unsafe_allow_html=True)

            if cand.flags:
                st.markdown(f"<div style='color:#e3b341; font-size:12px;'>⚠️ {len(cand.flags)} Flag(s) worth clarifying</div>", unsafe_allow_html=True)

            with st.expander("Why this bucket?"):
                st.caption(bucket_why)

            if st.button(f"Inspect Candidate Details", key=f"btn_sel_{cand.id}", use_container_width=True):
                st.session_state.selected_candidate_id = cand.id
                # Navigate to screen 3
                st.info(f"Selected {c_name_disp}. Switch to Screen 3: Candidate Detail.")

            st.markdown("</div>", unsafe_allow_html=True)
            col_idx += 1

    st.markdown("---")
    # Call D: Recruiter Evidence Chatbot with Verbatim Citations
    st.subheader("💬 Cited Recruiter Intelligence Q&A (Call D)")
    st.caption("Ask queries about pool evidence. Answers are synthesized strictly from verified evidence quotes with candidate citations.")

    q_input = st.text_input(
        "Ask about the candidate pool:",
        placeholder="e.g. Which candidates have verified production FastAPI experience and what were their projects?"
    )

    if st.button("🔎 Ask Copilot with Citations") and q_input.strip():
        with st.spinner("Searching verified candidate evidence pool..."):
            res = ask_pool(q_input, st.session_state.candidates)
            st.session_state.chat_history.append((q_input, res))

    if st.session_state.chat_history:
        for q, res in reversed(st.session_state.chat_history[-3:]):
            st.markdown(f"**Recruiter:** {q}")
            st.markdown(f"**Copilot:** {res.get('answer', '')}")
            if res.get("citations"):
                st.markdown("**Evidence Citations:**")
                for cit in res["citations"]:
                    c_label = cit.get("candidate", "Candidate")
                    c_label_disp = c_label if not bias_safe else "Candidate"
                    st.markdown(
                        f"- **{c_label_disp}** ({cit.get('requirement', '')}): "
                        f"<span class='quote-text'>\"{cit.get('quote', '')}\"</span>",
                        unsafe_allow_html=True
                    )
            st.markdown("---")


# ----------------------------------------------------------------------
# SCREEN 3: Candidate Detail
# ----------------------------------------------------------------------
elif active_screen.startswith("3."):
    st.title("🔍 Screen 3: Candidate Evidence & Audit Inspector")

    if not active_candidate:
        st.warning("No candidate selected. Please select a candidate from the sidebar.")
    else:
        c_name_disp = mask_for_bias_safe_display(active_candidate.name, active_candidate.anon_label, bias_safe)
        bucket, bucket_why = compute_bucket(active_candidate, st.session_state.role)
        clear_cnt = sum(1 for m in active_candidate.mappings if m.status == "Clear")
        total_cnt = len(st.session_state.role.requirements)

        # Summary Header Card
        st.markdown(f"""
        <div class='metric-card'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2>{c_name_disp}</h2>
                <div style='text-align:right;'>
                    <span style='font-size:16px; font-weight:700; color:#58a6ff;'>{bucket}</span><br/>
                    <span style='font-size:13px; color:#8b949e;'>{clear_cnt} of {total_cnt} Requirements Clear</span>
                </div>
            </div>
            <p style='margin-top:8px; color:#c9d1d9;'>{active_candidate.summary}</p>
        </div>
        """, unsafe_allow_html=True)

        # Consistency Flags (Neutral wording - Rule R5)
        if active_candidate.flags:
            st.subheader("⚠️ Consistency Observations (Worth Clarifying)")
            for flg in active_candidate.flags:
                st.markdown(render_flag_badge(flg.type, flg.description), unsafe_allow_html=True)

        # Requirements Evidence Map
        st.subheader("📋 Requirement Evidence Map")
        st.caption("Click any requirement to inspect its verified verbatim quote, source, and reasoning.")

        req_lookup = {r.id: r for r in st.session_state.role.requirements}

        for m in active_candidate.mappings:
            r_obj = req_lookup.get(m.requirement_id)
            r_text = r_obj.text if r_obj else m.requirement_id
            r_prio = r_obj.priority if r_obj else "must_have"

            status_badge = render_status_badge(m.status)
            source_badge = render_source_badge(m.source)
            prio_badge = render_priority_badge(r_prio)

            with st.expander(f"{m.requirement_id}: {r_text} | Status: {m.status}"):
                st.markdown(f"**Priority:** {prio_badge} &nbsp;|&nbsp; **Status:** {status_badge} &nbsp;|&nbsp; **Source:** {source_badge}", unsafe_allow_html=True)
                st.markdown(f"**Reasoning:** {m.reasoning}")

                if m.evidence:
                    st.markdown(f"**Verbatim Quote:** <span class='quote-text'>\"{m.evidence}\"</span>", unsafe_allow_html=True)
                else:
                    st.markdown("**Verbatim Quote:** *(None - Not found in resume)*")

                # Show status transitions if interview updated this requirement
                if m.history:
                    st.markdown("#### Evidence Transition History")
                    for h in m.history:
                        st.markdown(
                            f"- Transitioned from **{h.from_status}** to **{h.to_status}** ({h.timestamp})<br/>"
                            f"  *Reason:* {h.reason}<br/>"
                            f"  *Verbatim Quote:* <span class='quote-text'>\"{h.evidence}\"</span>",
                            unsafe_allow_html=True
                        )

        # Generated Interview Questions & Targeted Probes
        st.markdown("---")
        st.subheader("🎯 Targeted Interview Questions (AI Copilot Guidance)")
        st.caption("Generated specifically to address unverified and partial criteria:")
        if active_candidate.interview_questions:
            for q in active_candidate.interview_questions:
                st.markdown(f"• **Requirement {q.get('requirement_id')}:** {q.get('question')}")
                if q.get("follow_up"):
                    st.markdown(f"  *Follow-up Probe:* {q.get('follow_up')}")
        else:
            st.info("All requirements currently have clear verified evidence.")

        # Recruiter Audit Panel
        st.markdown("---")
        with st.expander("🛡️ Recruiter Audit Log (Immutable Timeline)", expanded=False):
            st.caption("Complete chronological record of all models, timestamps, inputs, and state updates:")
            for a in reversed(active_candidate.audit):
                st.markdown(
                    f"<div style='border-bottom:1px solid #21262d; padding:6px 0; font-size:12px;'>"
                    f"<span style='color:#58a6ff;'>[{a.timestamp}]</span> "
                    f"<strong>{a.insight}</strong> &nbsp;|&nbsp; "
                    f"<em>Model: {a.model}</em><br/>"
                    f"<span style='color:#8b949e;'>Inputs: {a.inputs_used}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )


# ----------------------------------------------------------------------
# SCREEN 4: Interview Room (The Hero Loop)
# ----------------------------------------------------------------------
elif active_screen.startswith("4."):
    st.title("🎙️ Screen 4: Interview Room & Real-Time Evidence Update")
    st.markdown("Conduct live interviews, paste candidate answers, and watch evidence update dynamically in **<5 seconds**.")

    if not active_candidate:
        st.warning("Please select a candidate.")
    else:
        c_name_disp = mask_for_bias_safe_display(active_candidate.name, active_candidate.anon_label, bias_safe)

        # Candidate Header & Live Coverage Bar
        clear_cnt = sum(1 for m in active_candidate.mappings if m.status == "Clear")
        total_cnt = len(st.session_state.role.requirements)
        coverage_pct = (clear_cnt / total_cnt) if total_cnt > 0 else 0

        st.markdown(f"### Interviewing: **{c_name_disp}**")
        st.progress(coverage_pct, text=f"Evidence Coverage: {clear_cnt} of {total_cnt} Requirements Clear ({int(coverage_pct*100)}%)")

        col_q, col_note = st.columns([1, 1])

        with col_q:
            st.subheader("Targeted Interview Questions")
            # Select target requirement
            unverified_reqs = [
                m.requirement_id for m in active_candidate.mappings
                if m.status in ["Partial", "Unclear", "Missing"]
            ] or [m.requirement_id for m in active_candidate.mappings]

            target_req_id = st.selectbox(
                "Focus Requirement",
                options=unverified_reqs,
                index=0 if "R3" not in unverified_reqs else unverified_reqs.index("R3")
            )

            target_m = next(m for m in active_candidate.mappings if m.requirement_id == target_req_id)
            target_r = next((r for r in st.session_state.role.requirements if r.id == target_req_id), None)

            st.markdown(f"**Criterion ({target_req_id}):** {target_r.text if target_r else ''}")
            st.markdown(f"**Current Status:** {render_status_badge(target_m.status)}", unsafe_allow_html=True)

            # Suggest question
            matching_q = next((q["question"] for q in active_candidate.interview_questions if q.get("requirement_id") == target_req_id), None)
            active_q_text = matching_q or f"Can you describe your direct hands-on experience with {target_r.text if target_r else target_req_id} in production?"
            st.info(f"💡 **Suggested Question:**\n\n{active_q_text}")

            # 1-Click Hero Demo Button
            if active_candidate.id == "c2" and target_req_id == "R3":
                st.markdown("#### ⚡ 1-Click Hero Demonstration")
                if st.button("Insert Demo Answer (Candidate 2 Docker Validation)", use_container_width=True):
                    with open(os.path.join(DEMO_DIR, "answers", "c2_docker_answer.txt"), "r", encoding="utf-8") as f:
                        demo_answer = f.read()
                    st.session_state.prefill_answer = demo_answer
                    st.rerun()

        with col_note:
            st.subheader("Interviewer Notes & Answer Intake")
            curr_answer = st.session_state.get("prefill_answer", "")
            answer_input = st.text_area("Live Candidate Response:", value=curr_answer, height=220)

            if st.button("🚀 Analyze Answer & Update Evidence (Call C)", use_container_width=True, type="primary"):
                if not answer_input.strip():
                    st.warning("Please enter or paste an answer.")
                else:
                    with st.spinner("Analyzing candidate response and verifying verbatim quote..."):
                        t0 = time.time()
                        updated_cand = analyze_answer(active_candidate, target_req_id, active_q_text, answer_input)
                        elapsed = time.time() - t0

                        # Update state
                        for idx, c in enumerate(st.session_state.candidates):
                            if c.id == updated_cand.id:
                                st.session_state.candidates[idx] = updated_cand
                                break

                        st.session_state.prefill_answer = ""
                        st.success(f"Evidence updated in {elapsed:.2f} seconds!")
                        st.rerun()

        # Dynamic Status-Change Feed
        st.markdown("---")
        st.subheader("📢 Real-Time Evidence Feed (Status Changes)")
        has_any_transition = False

        for m in active_candidate.mappings:
            for ch in m.history:
                has_any_transition = True
                st.markdown(f"""
                <div class='status-feed-card'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <strong>Requirement {m.requirement_id}</strong>
                        <div>
                            {render_status_badge(ch.from_status)} ➔ {render_status_badge(ch.to_status)}
                        </div>
                    </div>
                    <div style='margin:8px 0;'><strong>Transition Reason:</strong> {ch.reason}</div>
                    <div><strong>Verbatim Interview Quote:</strong> <span class='quote-text'>"{ch.evidence}"</span></div>
                </div>
                """, unsafe_allow_html=True)

        if not has_any_transition:
            st.info("No status changes recorded yet for this candidate. Conduct an interview or click 'Insert Demo Answer' above.")


# ----------------------------------------------------------------------
# SCREEN 5: Compare & Report
# ----------------------------------------------------------------------
elif active_screen.startswith("5."):
    st.title("⚖️ Screen 5: Multi-Candidate Comparison & Recruiter Report")

    tab_compare, tab_report = st.tabs(["📊 Side-by-Side Comparison", "📄 Explainable Recruiter Report"])

    with tab_compare:
        st.subheader("Side-by-Side Requirement Evidence Matrix")
        st.caption("Rule R1 Compliance: Compares 2-3 candidates strictly on evidence quotes without ranking or scoring.")

        cand_select_ids = st.multiselect(
            "Select 2 or 3 candidates to compare:",
            options=[c.id for c in st.session_state.candidates],
            default=[c.id for c in st.session_state.candidates[:3]],
            format_func=lambda cid: mask_for_bias_safe_display(
                next(c.name for c in st.session_state.candidates if c.id == cid),
                next(c.anon_label for c in st.session_state.candidates if c.id == cid),
                bias_safe
            )
        )

        if len(cand_select_ids) < 2:
            st.warning("Please select at least 2 candidates to compare.")
        else:
            selected_cands = [c for c in st.session_state.candidates if c.id in cand_select_ids]
            
            # Header columns
            header_cols = st.columns([2] + [3] * len(selected_cands))
            header_cols[0].markdown("### Requirement")
            for idx, sc in enumerate(selected_cands):
                c_name_col = mask_for_bias_safe_display(sc.name, sc.anon_label, bias_safe)
                b_fit, _ = compute_bucket(sc, st.session_state.role)
                c_clear = sum(1 for m in sc.mappings if m.status == "Clear")
                header_cols[idx + 1].markdown(f"### {c_name_col}\n**{b_fit}** ({c_clear}/{len(st.session_state.role.requirements)} Clear)")

            st.markdown("---")

            for req in st.session_state.role.requirements:
                row_cols = st.columns([2] + [3] * len(selected_cands))
                row_cols[0].markdown(f"**{req.id}**<br/><small>{req.text}</small>", unsafe_allow_html=True)

                for idx, sc in enumerate(selected_cands):
                    m = next((m for m in sc.mappings if m.requirement_id == req.id), None)
                    if m:
                        st_badge = render_status_badge(m.status)
                        src_badge = render_source_badge(m.source)
                        q_text = f"<span class='quote-text'>\"{m.evidence}\"</span>" if m.evidence else "<i>(No quote)</i>"
                        row_cols[idx + 1].markdown(
                            f"{st_badge} {src_badge}<br/>{q_text}",
                            unsafe_allow_html=True
                        )
                st.markdown("<hr style='margin:6px 0; border-color:#21262d;'/>", unsafe_allow_html=True)

    with tab_report:
        st.subheader("Recruiter Evidence & Verification Report")
        if not active_candidate:
            st.warning("Select a candidate.")
        else:
            c_name_disp = mask_for_bias_safe_display(active_candidate.name, active_candidate.anon_label, bias_safe)
            b_fit, b_why = compute_bucket(active_candidate, st.session_state.role)

            st.markdown(f"### Candidate: **{c_name_disp}** &nbsp;|&nbsp; Role: **{st.session_state.role.title}**")
            st.markdown(f"**Evaluation Summary:** {b_fit} – {b_why}")

            # Breakdown
            col_v, col_nv = st.columns(2)
            with col_v:
                st.markdown("#### ✅ Validated Criteria (Clear)")
                clears = [m for m in active_candidate.mappings if m.status == "Clear"]
                if clears:
                    for m in clears:
                        st.markdown(f"• **{m.requirement_id}**: <span class='quote-text'>\"{m.evidence}\"</span>", unsafe_allow_html=True)
                else:
                    st.info("None verified yet.")

            with col_nv:
                st.markdown("#### ⏳ Still Needs Validation / Focus Areas")
                unclear_gaps = [m for m in active_candidate.mappings if m.status in ["Partial", "Unclear", "Missing"]]
                if unclear_gaps:
                    for m in unclear_gaps:
                        st.markdown(f"• **{m.requirement_id}** ({m.status}): {m.reasoning}")
                else:
                    st.success("All requirements verified clear!")

            st.markdown("---")
            st.markdown("#### Human Recruiter Decision & Sign-off Notes (R2 Compliance)")
            st.text_area("Recruiter Interview Sign-Off Notes:", placeholder="Enter observations and hiring manager notes here...")

            # PDF Download
            pdf_bytes = generate_candidate_pdf(active_candidate, st.session_state.role, bias_safe=bias_safe)
            st.download_button(
                label="📥 Download Official Recruiter PDF Report",
                data=pdf_bytes,
                file_name=f"hireflow_report_{active_candidate.id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
