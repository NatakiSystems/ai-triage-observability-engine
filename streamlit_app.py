import glob
import json
import os
from pathlib import Path
from datetime import datetime
import streamlit as st

# 1. PAGE SETUP & ENTERPRISE BRANDING
st.set_page_config(
    page_title="Northstar Support Co. | Control Console",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

POLAR_NAVY = "#0B1B3D"
GUIDING_COBALT = "#1E56A0"
AURORA_CYAN = "#00C2CB"
GLACIER_MIST = "#F4F7FB"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {GLACIER_MIST};
    }}
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }}
    .brand-card {{
        background: white;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(11, 27, 61, 0.08);
        box-shadow: 0 4px 14px rgba(11, 27, 61, 0.04);
        margin-bottom: 16px;
    }}
    .flag-box {{
        background-color: #FFF4E5;
        border-left: 5px solid #FF9800;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 12px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# 2. BULLETPROOF DATA LOADERS
QUEUE_PATH = os.path.join(os.path.dirname(__file__), "logs", "approval_queue.json")

def get_latest_log_path():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    logs = sorted(glob.glob(os.path.join(log_dir, "*.jsonl")))
    return logs[-1] if logs else None

def load_queue():
    if os.path.exists(QUEUE_PATH):
        try:
            with open(QUEUE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []

def load_events(log_path):
    events = []
    if log_path and os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        if isinstance(record, dict):
                            events.append(record)
                    except Exception:
                        pass
    return events

# 3. STATE & DATA INITIALIZATION
if "queue" not in st.session_state:
    st.session_state.queue = load_queue()

if "decisions" not in st.session_state:
    st.session_state.decisions = {}

# 4. BRAND HEADER
logo_path = Path("northstar_support_logo.png")
if logo_path.exists():
    st.image(str(logo_path), width=340)
else:
    st.markdown(
        f"<h2 style='color:{POLAR_NAVY}; margin:0;'>NORTHSTAR SUPPORT CO.</h2>",
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <div style="font-size: 1.25rem; font-weight: 700; color: {POLAR_NAVY}; margin-top: 10px; margin-bottom: 20px; letter-spacing: 0.02em;">
        Guided by Care. Driven by Precision. <span style="color: {GUIDING_COBALT}; font-weight: 400;">| Operational Control & Governance Console</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# 5. REAL-TIME METRICS CALCULATION
latest_log = get_latest_log_path()
events = load_events(latest_log)

tickets_seen = set()
auto_sent_count = 0
escalated_count = 0
timestamps = []

for ev in events:
    t_id = ev.get("ticket_id")
    if t_id:
        tickets_seen.add(t_id)
    ev_type = ev.get("event_type")
    if ev_type == "auto_sent":
        auto_sent_count += 1
    elif ev_type == "escalated_to_human":
        escalated_count += 1
    ts = ev.get("timestamp")
    if ts:
        try:
            clean_ts = ts.replace("Z", "+00:00")
            timestamps.append(datetime.fromisoformat(clean_ts))
        except Exception:
            pass

total_processed = len(tickets_seen) if tickets_seen else 0
auto_rate = round((auto_sent_count / total_processed * 100), 1) if total_processed > 0 else 0.0

elapsed_sec = 0.0
sec_per_ticket = 0.0
if len(timestamps) >= 2:
    timestamps.sort()
    elapsed_sec = (timestamps[-1] - timestamps[0]).total_seconds()
    if total_processed > 0:
        sec_per_ticket = round(elapsed_sec / total_processed, 2)

pending_queue = len(
    [
        item
        for item in st.session_state.queue
        if (item.get("ticket") or {}).get("ticket_id") not in st.session_state.decisions
    ]
)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Tickets Ingested", total_processed)
with col_m2:
    st.metric("Automation Rate", f"{auto_rate}%")
with col_m3:
    st.metric("Avg Latency / Ticket", f"{sec_per_ticket}s" if sec_per_ticket > 0 else "N/A")
with col_m4:
    st.metric("Pending Human Review", pending_queue)

st.divider()

# 6. TABBED WORKSPACE
tab_queue, tab_audit = st.tabs(
    ["🛡️ Supervisor Review Queue", "🔍 Audit Trail & Telemetry Trace"]
)

# TAB 1: SUPERVISOR REVIEW QUEUE
with tab_queue:
    st.subheader("Human Checkpoint: Flagged Exception Inbox")
    st.write("Review, modify, or approve drafts that triggered safety or policy thresholds.")

    pending_items = [
        item
        for item in st.session_state.queue
        if (item.get("ticket") or {}).get("ticket_id") not in st.session_state.decisions
    ]

    if not pending_items:
        st.success("All exceptions have been reviewed! The approval queue is clean.")
    else:
        for idx, item in enumerate(pending_items):
            ticket = item.get("ticket") or {}
            verdict = item.get("verdict") or {}
            ticket_id = ticket.get("ticket_id", f"ticket_{idx}")
            reason = verdict.get("reasoning", "Flagged for human supervisor review.")
            issues = verdict.get("issues", [])
            draft_text = item.get("draft", "(No draft text generated)")
            attempts = item.get("attempts", 1)

            st.markdown(
                f"""
                <div class="brand-card">
                    <h4 style="color: {POLAR_NAVY}; margin:0;">Ticket {ticket_id}: {ticket.get('subject', '(No Subject)')}</h4>
                    <p style="color:#667085; font-size:0.9rem; margin-top:4px;"><b>Customer:</b> {ticket.get('customer_name', 'Customer')} | <b>Email:</b> {ticket.get('customer_email', 'N/A')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_cust, col_draft = st.columns([1, 1])
            with col_cust:
                st.markdown("**Customer Message:**")
                st.info(ticket.get("body", "(No body text)"))
                st.markdown(
                    f"""
                    <div class="flag-box">
                        <b style="color:#B76E00;">⚠️ FLAGGED BECAUSE:</b><br>{reason}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if issues:
                    st.markdown("**Identified Issues:**")
                    for iss in issues:
                        st.markdown(f"- {iss}")

            with col_draft:
                st.markdown(f"**Generated Draft (Attempt {attempts}):**")
                edited_draft = st.text_area(
                    label=f"Edit Draft for {ticket_id}",
                    value=draft_text,
                    height=160,
                    key=f"edit_{ticket_id}_{idx}",
                    label_visibility="collapsed",
                )
                sup_notes = st.text_input(
                    "Optional Supervisor Note:",
                    placeholder="e.g., Adjusted tone for empathy",
                    key=f"note_{ticket_id}_{idx}",
                )

                b_col1, b_col2, b_col3 = st.columns(3)
                with b_col1:
                    if st.button("✅ Approve", key=f"btn_app_{ticket_id}_{idx}", use_container_width=True):
                        st.session_state.decisions[ticket_id] = {
                            "decision": "approved",
                            "final_text": edited_draft,
                            "note": sup_notes,
                        }
                        st.rerun()
                with b_col2:
                    if st.button("❌ Reject", key=f"btn_rej_{ticket_id}_{idx}", use_container_width=True):
                        st.session_state.decisions[ticket_id] = {
                            "decision": "rejected",
                            "note": sup_notes,
                        }
                        st.rerun()
                with b_col3:
                    if st.button("⏭️ Skip", key=f"btn_skp_{ticket_id}_{idx}", use_container_width=True):
                        st.session_state.decisions[ticket_id] = {
                            "decision": "skipped",
                            "note": sup_notes,
                        }
                        st.rerun()

            st.divider()

    if st.session_state.decisions:
        with st.expander("📋 View Completed Supervisor Decisions This Session", expanded=False):
            st.json(st.session_state.decisions)

# TAB 2: AUDIT TRAIL & TELEMETRY TRACE
with tab_audit:
    st.subheader("System Flight Recorder: Immutable Audit Trail")
    st.write("Inspect end-to-end reasoning, tool retrievals, and QA checks for any ticket.")

    if not events:
        st.warning("No run logs found in logs/ directory. Run python main.py first.")
    else:
        tickets_map = {}
        for ev in events:
            t_id = ev.get("ticket_id") or "System Level"
            if t_id not in tickets_map:
                tickets_map[t_id] = []
            tickets_map[t_id].append(ev)

        selected_ticket = st.selectbox(
            "Select Ticket ID to Inspect Trace:",
            options=list(tickets_map.keys()),
        )

        if selected_ticket:
            ticket_events = tickets_map[selected_ticket]
            st.markdown(f"#### Lifecycle Trace for {selected_ticket}")

            for ev in ticket_events:
                timestamp = str(ev.get("timestamp", "00:00:00"))
                event_type = str(ev.get("event_type", "event"))
                payload = ev.get("payload") or {}
                if not isinstance(payload, dict):
                    payload = {"raw_data": payload}

                if event_type == "triage_complete":
                    with st.expander(f"🏷️ [{timestamp}] Step 1: Triage Classification Complete", expanded=True):
                        cat = payload.get("category") or ev.get("category", "N/A")
                        pri = payload.get("priority") or ev.get("priority", "P2")
                        conf = payload.get("confidence") or ev.get("confidence", "N/A")
                        st.write(f"**Category:** {cat} | **Priority:** {pri} | **Confidence:** {conf}")
                        st.json(payload if payload != {"raw_data": None} else ev)

                elif event_type == "policy_retrieved":
                    with st.expander(f"📚 [{timestamp}] Step 2: Policy Retrieved (Tool Call)", expanded=True):
                        chunk = payload.get("chunk_id") or payload.get("policy_id") or ev.get("chunk_id", "POL-REF")
                        text_val = payload.get("policy_text") or payload.get("retrieved_text") or ev.get("policy_text") or "Policy retrieved successfully."
                        st.write(f"**Policy Ref:** {chunk}")
                        st.info(text_val)

                elif event_type == "draft_created":
                    attempt_no = payload.get("attempt") or ev.get("attempt", 1)
                    draft_val = payload.get("draft") or payload.get("draft_reply") or ev.get("draft", "")
                    with st.expander(f"✍️ [{timestamp}] Step 3: Response Drafted (Attempt {attempt_no})", expanded=True):
                        st.text_area(
                            "Draft Content:",
                            value=str(draft_val),
                            height=100,
                            disabled=True,
                            key=f"trace_draft_{selected_ticket}_{timestamp}",
                        )

                elif event_type == "critic_verdict":
                    with st.expander(f"⚖️ [{timestamp}] Step 4: Critic QA Audit", expanded=True):
                        passed = payload.get("passed", ev.get("passed", False))
                        reason_str = payload.get("reasoning") or payload.get("feedback") or ev.get("reasoning", "Review completed.")
                        if passed:
                            st.success(f"Audit Passed: {reason_str}")
                        else:
                            st.error(f"Audit Flagged: {reason_str}")
                        st.json(payload if payload != {"raw_data": None} else ev)

                elif event_type in ("auto_sent", "escalated_to_human"):
                    with st.expander(f"🚀 [{timestamp}] Step 5: Dispatch Action", expanded=True):
                        if event_type == "auto_sent":
                            st.success("✅ **Status:** Auto-Sent directly to customer.")
                        else:
                            st.warning("⚠️ **Status:** Escalated to human approval queue.")
                        st.json(payload if payload != {"raw_data": None} else ev)

                else:
                    with st.expander(f"📌 [{timestamp}] Event: {event_type}", expanded=False):
                        st.json(ev)

# 7. TEAM FOOTER (SIDE-BY-SIDE BRANDING)
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()

col_team_logo, col_team_roster = st.columns([1.2, 1.8], gap="large")
with col_team_logo:
    team_logo_path = Path("team_logo.png")
    if team_logo_path.exists():
        st.image(str(team_logo_path), use_container_width=True)
    else:
        st.markdown(
            f"""
            <div style="font-size: 1.4rem; font-weight: 800; color: {POLAR_NAVY};">
                COME ON BACK
            </div>
            <div style="font-size: 0.85rem; color: {AURORA_CYAN}; font-weight: 600;">
                AI SYSTEMS CONSULTANCY
            </div>
            <div style="font-size: 0.8rem; color: #667085; font-style: italic; margin-top: 4px;">
                Engineered for Speed. Verified for Trust.
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_team_roster:
    st.markdown(
        f"""
        <div style="background: white; border-radius: 10px; padding: 18px 24px; border: 1px solid rgba(11, 27, 61, 0.08); box-shadow: 0 2px 10px rgba(11, 27, 61, 0.03);">
            <div style="font-size: 0.8rem; font-weight: 700; color: {GUIDING_COBALT}; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px;">
                Engineering & Project Delivery Team
            </div>
            <div style="display: grid; grid-template-columns: 1fr; gap: 6px; font-size: 0.92rem; color: {POLAR_NAVY};">
                <div><b>Orchestrator Engineer:</b> Enrique Quezada</div>
                <div><b>Integration Engineer:</b> Lance Gonzalez</div>
                <div><b>Prompt Engineer:</b> Mitchy Derose</div>
                <div><b>QA / Critic Engineer:</b> Julian Seiferth</div>
                <div><b>Logging & Observability Engineer:</b> Nataki Boykin</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )