import streamlit as st
import requests
import json

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Hate Speech Moderation Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .badge-clean { background-color: #059669; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-mild { background-color: #d97706; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-hate { background-color: #dc2626; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-severe { background-color: #7f1d1d; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CONFIGURATION & STATE MANAGEMENT
# ==========================================
# Toggle USE_MOCK to True for local testing, or False for FastAPI Live Backend connection
USE_MOCK = True  
API_BASE_URL = "http://localhost:8000"

if "queue_data" not in st.session_state:
    st.session_state.queue_data = []

# Mock initial queue data for offline UI testing
MOCK_QUEUE = [
    {
        "post_id": 101,
        "post_text": "You are completely useless and nobody wants you here!",
        "predicted_severity": "Hate Speech",
        "confidence_score": "88%",
        "dialect": "English",
        "timestamp": "2026-10-08 10:15 AM"
    },
    {
        "post_id": 102,
        "post_text": "This movie was absolute trash, don't waste your money.",
        "predicted_severity": "Mild Hate",
        "confidence_score": "72%",
        "dialect": "Slang",
        "timestamp": "2026-10-08 10:18 AM"
    },
    {
        "post_id": 103,
        "post_text": "Go back where you came from before we make you regret it.",
        "predicted_severity": "Severe Threat",
        "confidence_score": "95%",
        "dialect": "English",
        "timestamp": "2026-10-08 10:22 AM"
    }
]

# Helper function to load review queue
def fetch_review_queue(mod_id):
    if USE_MOCK:
        return st.session_state.get("queue_data", MOCK_QUEUE)
    else:
        try:
            res = requests.get(f"{API_BASE_URL}/api/moderator-queue/{mod_id}")
            if res.status_code == 200:
                return res.json()
            else:
                st.error(f"Failed to fetch queue from backend (Status Code: {res.status_code})")
                return []
        except Exception as e:
            st.error(f"Backend API offline: {e}")
            return []

# Helper function to submit moderation actions
def send_moderation_action(mod_id, post_id, action_type):
    if USE_MOCK:
        # Update local state in mock mode
        if "queue_data" in st.session_state and st.session_state.queue_data:
            st.session_state.queue_data = [item for item in st.session_state.queue_data if item["post_id"] != post_id]
        else:
            global MOCK_QUEUE
            MOCK_QUEUE = [item for item in MOCK_QUEUE if item["post_id"] != post_id]
        st.toast(f"Action Submitted: {action_type} for Post #{post_id}!", icon="✅")
        st.rerun()
    else:
        try:
            payload = {
                "moderator_id": mod_id,
                "post_id": post_id,
                "action": action_type
            }
            res = requests.post(f"{API_BASE_URL}/api/moderator-action", json=payload)
            if res.status_code == 200:
                st.toast(f"Action Recorded: {action_type}", icon="✅")
                st.rerun()
            else:
                st.error(f"Failed to process action: {res.text}")
        except Exception as e:
            st.error(f"Error connecting to server: {e}")

# Initialize session queue if empty
if not st.session_state.queue_data and USE_MOCK:
    st.session_state.queue_data = MOCK_QUEUE.copy()

# ==========================================
# SIDEBAR: MODERATOR PROFILE & CSP METRICS
# ==========================================
with st.sidebar:
    st.title("👤 Moderator Profile")
    
    active_mod_id = st.number_input("Active Moderator ID", min_value=1, max_value=10, value=1, step=1)
    
    st.markdown("---")
    st.write("**Platform Source:**", "⚙️ Mock Testing Pipeline" if USE_MOCK else "🟢 API Integration Pipeline")
    st.write("**Assigned Dialects/Skills:**", "English, Slang" if active_mod_id % 2 != 0 else "Hindi, Urdu")
    
    st.markdown("---")
    st.subheader("Workload Capacity (CSP)")
    
    current_items = len(fetch_review_queue(active_mod_id))
    max_capacity = 5
    capacity_pct = min(current_items / max_capacity, 1.0)
    
    st.progress(capacity_pct)
    st.caption(f"Active Load: **{current_items} / {max_capacity}** Assigned")
    
    st.markdown("---")
    if st.button("🔄 Refresh Review Queue", use_container_width=True):
        if USE_MOCK:
            st.session_state.queue_data = MOCK_QUEUE.copy()
            st.toast("Mock Queue Refreshed!", icon="ℹ️")
        st.rerun()

# ==========================================
# MAIN PANEL: HEADER
# ==========================================
st.markdown("""
    <div class="main-header">
        <h1>🛡️ Hate Speech Content Moderation Dashboard</h1>
        <p>Hybrid AI Classification & CSP Workload-Routed Flagged Content Review</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# FEATURE: INTERACTIVE CUSTOM COMMENT TESTER
# ==========================================
with st.expander("🧪 Test Custom Comment / Live Ingestion", expanded=False):
    st.markdown("Type a custom post or comment below to run it through the system:")
    
    user_input = st.text_area("Enter comment text:", placeholder="e.g., You are so stupid and useless!", key="custom_input_text")
    
    if st.button("Analyze & Route Comment", type="primary"):
        if user_input.strip():
            if USE_MOCK:
                text_lower = user_input.lower()
                if any(w in text_lower for w in ["kill", "attack", "destroy", "die"]):
                    severity = "Severe Threat"
                    confidence = "96%"
                    badge_class = "badge-severe"
                elif any(w in text_lower for w in ["hate", "stupid", "idiot", "dumb", "useless"]):
                    severity = "Hate Speech"
                    confidence = "88%"
                    badge_class = "badge-hate"
                elif any(w in text_lower for w in ["annoying", "bad", "fool", "trash"]):
                    severity = "Mild Hate"
                    confidence = "72%"
                    badge_class = "badge-mild"
                else:
                    severity = "Clean"
                    confidence = "94%"
                    badge_class = "badge-clean"

                # Add newly created post directly into active mock queue
                new_post = {
                    "post_id": len(st.session_state.queue_data) + 201,
                    "post_text": user_input,
                    "predicted_severity": severity,
                    "confidence_score": confidence,
                    "dialect": "English",
                    "timestamp": "Just Now"
                }
                st.session_state.queue_data.insert(0, new_post)
                
                st.success("Analysis Complete & Added to Review Queue!")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Predicted Severity:** <span class='{badge_class}'>{severity}</span>", unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"**Model Confidence:** `{confidence}`")
                st.rerun()

            else:
                # Live FastAPI Endpoint Request
                try:
                    res = requests.post(f"{API_BASE_URL}/api/ingest", json={"text": user_input})
                    if res.status_code == 200:
                        st.success("Post successfully ingested into backend database!")
                        st.rerun()
                    else:
                        st.error(f"Backend API error: {res.status_code}")
                except Exception as e:
                    st.error(f"Could not connect to FastAPI server: {e}")
        else:
            st.warning("Please enter some text before submitting.")

st.markdown("---")

# ==========================================
# MAIN PANEL: REVIEW QUEUE RENDERING
# ==========================================
queue_items = fetch_review_queue(active_mod_id)

if not queue_items:
    st.info("🎉 No active flagged content in queue for this moderator.")
else:
    st.subheader(f"📋 Assigned Queue Items ({len(queue_items)})")
    
    for item in queue_items:
        with st.container():
            st.markdown("---")
            
            # Badge selection based on severity
            sev = item.get("predicted_severity", "Clean")
            if sev == "Severe Threat":
                badge_html = f"<span class='badge-severe'>{sev}</span>"
            elif sev == "Hate Speech":
                badge_html = f"<span class='badge-hate'>{sev}</span>"
            elif sev == "Mild Hate":
                badge_html = f"<span class='badge-mild'>{sev}</span>"
            else:
                badge_html = f"<span class='badge-clean'>{sev}</span>"
            
            # Header info
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"**Post ID:** #{item.get('post_id')}")
            with c2:
                st.markdown(f"**Severity:** {badge_html}", unsafe_allow_html=True)
            with c3:
                st.markdown(f"**AI Confidence:** `{item.get('confidence_score', 'N/A')}`")
            
            # Post Content Box
            st.info(f"💬 **Content:** \"{item.get('post_text')}\"")
            st.caption(f"🕒 Timestamp: {item.get('timestamp', 'N/A')} | Dialect Tag: {item.get('dialect', 'General')}")
            
            # Enforcement Buttons
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if st.button("🟢 Approve / Clean", key=f"app_{item['post_id']}", use_container_width=True):
                    send_moderation_action(active_mod_id, item['post_id'], "Approve")
            with b2:
                if st.button("🟡 Warning Reply", key=f"warn_{item['post_id']}", use_container_width=True):
                    send_moderation_action(active_mod_id, item['post_id'], "Warning Reply")
            with b3:
                if st.button("🟠 Delete Post", key=f"del_{item['post_id']}", use_container_width=True):
                    send_moderation_action(active_mod_id, item['post_id'], "Delete Post")
            with b4:
                if st.button("🔴 Delete + Strike", key=f"strike_{item['post_id']}", use_container_width=True):
                    send_moderation_action(active_mod_id, item['post_id'], "Delete + Issue Strike")