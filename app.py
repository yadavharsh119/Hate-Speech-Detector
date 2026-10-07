import os
import requests
import streamlit as st

# Configure Dashboard Layout
st.set_page_config(
    page_title="Hate Speech Moderation Dashboard",
    page_icon="🛡️",
    layout="wide",
)

# Custom CSS for UI Enhancement
st.markdown(
    """
    <style>
    /* Main Background Accent */
    .main {
        background-color: #0e1117;
    }
    
    /* Header Card Styling */
    .header-card {
        background: linear-gradient(135deg, #1e2640 0%, #0f172a 100%);
        padding: 24px;
        border-radius: 12px;
        border-left: 6px solid #6366f1;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* Content Preview Card */
    .content-box {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #334155;
        font-size: 1.15rem;
        color: #f8fafc;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    
    /* Dynamic Severity Badges */
    .badge-clean {
        background-color: #10b981;
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    .badge-moderate {
        background-color: #f59e0b;
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    .badge-severe {
        background-color: #ef4444;
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Backend API Configuration (FastAPI default port)
BACKEND_API_URL = "http://localhost:8000/api"
USE_MOCK = True  # Connected directly to FastAPI backend


# Helper Function to Load Assigned Queue
def load_assigned_tweets(moderator_id: int):
    if USE_MOCK:
        return [
            {
                "id": 1,
                "tweet_id_str": "17981234567890123",
                "text": "This picture is not looking good, disappointing post.",
                "author_handle": "@insta_user_1",
                "ai_category": "Clean",
                "confidence_score": 0.92,
                "status": "assigned",
                "created_at": "2026-10-07T09:15:00",
            },
            {
                "id": 2,
                "tweet_id_str": "17981234567890124",
                "text": "Go back to where you came from, nobody wants you here!",
                "author_handle": "@troll_user99",
                "ai_category": "Moderate Hate",
                "confidence_score": 0.88,
                "status": "assigned",
                "created_at": "2026-10-07T09:18:22",
            },
            {
                "id": 3,
                "tweet_id_str": "17981234567890125",
                "text": "We will find you and make sure you pay for this.",
                "author_handle": "@threat_actor_0",
                "ai_category": "Severe Hate",
                "confidence_score": 0.97,
                "status": "assigned",
                "created_at": "2026-10-07T09:22:10",
            },
        ]
    else:
        try:
            res = requests.get(f"{BACKEND_API_URL}/moderator-queue/{moderator_id}")
            if res.status_code == 200:
                return res.json()
            else:
                st.error(f"Error fetching queue: HTTP {res.status_code}")
                return []
        except Exception as e:
            st.error(f"Backend API offline: {e}")
            return []


# Helper Function to Submit Enforcement Actions
def send_moderation_action(tweet_id: int, moderator_id: int, verdict: str, action_taken: str):
    payload = {
        "tweet_id": tweet_id,
        "moderator_id": moderator_id,
        "verdict": verdict,
        "action_taken": action_taken,
    }

    if USE_MOCK:
        st.toast(f"Action Recorded (Mock): {action_taken} for Tweet #{tweet_id}", icon="✅")
        return True
    else:
        try:
            res = requests.post(f"{BACKEND_API_URL}/moderator-action", json=payload)
            if res.status_code == 200:
                data = res.json()
                st.toast(
                    f"Enforcement triggered: {action_taken} (Status: {data.get('enforcement_status')})",
                    icon="🚀",
                )
                return True
            else:
                st.error(f"Failed to submit action: {res.text}")
                return False
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")
            return False


# --- SIDEBAR: Moderator Profile & CSP Controls ---
st.sidebar.title("🛡️ Moderator Profile")

mod_id = st.sidebar.number_input("Active Moderator ID", min_value=1, value=1, step=1)

st.sidebar.markdown("**Platform Source:** `API Integration Pipeline`")
st.sidebar.markdown("**Assigned Dialects/Skills:** `English`, `Slang`")
st.sidebar.divider()

# Refresh Queue Control
if st.sidebar.button("🔄 Refresh Review Queue", use_container_width=True):
    st.rerun()

# Workload Capacity Section
MAX_CAPACITY = 5
tweets = load_assigned_tweets(mod_id)
active_count = len(tweets)

st.sidebar.subheader("Workload Capacity (CSP)")
st.sidebar.progress(min(active_count / MAX_CAPACITY, 1.0))
st.sidebar.write(f"Active Load: **{active_count} / {MAX_CAPACITY} Assigned**")
st.sidebar.divider()

# --- MAIN DASHBOARD HEADER ---
st.markdown(
    """
    <div class="header-card">
        <h1 style="color: #ffffff; margin:0;">🛡️ Hate Speech Content Moderation Dashboard</h1>
        <p style="color: #94a3b8; margin-top: 5px; font-size: 1.05rem;">
            Hybrid AI Classification & CSP Workload-Routed Flagged Content Review
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not tweets:
    st.info("No active flagged content in queue for this moderator.")
else:
    # Sidebar selection for active tweet
    tweet_options = {
        f"Item #{t['id']} - [{t.get('ai_category', 'Unclassified')}]": t for t in tweets
    }
    selected_label = st.sidebar.radio("Select Flagged Content:", list(tweet_options.keys()))
    active_tweet = tweet_options[selected_label]

    # --- MAIN CONTENT LAYOUT (2 COLUMNS) ---
    col_left, col_right = st.columns([1.2, 1])

    # Left Column: Flagged Content & AI Metadata
    with col_left:
        st.subheader("📋 Content Details & AI Classification")

        cat = active_tweet.get("ai_category", "Unknown")
        confidence = active_tweet.get("confidence_score", 0.0)
        conf_pct = f"{int(confidence * 100)}%" if confidence else "N/A"

        # Determine Badge Style
        if "clean" in cat.lower():
            badge_class = "badge-clean"
        elif "severe" in cat.lower():
            badge_class = "badge-severe"
        else:
            badge_class = "badge-moderate"

        st.markdown(
            f"**Author:** `{active_tweet.get('author_handle', '@unknown')}` | "
            f"**Database ID:** `{active_tweet['id']}`"
        )
        st.markdown(f"**Platform Content ID:** `{active_tweet.get('tweet_id_str', 'N/A')}`")
        st.markdown(f"**Ingested At:** {active_tweet.get('created_at', 'N/A')}")

        st.markdown(
            f'<div class="content-box">"{active_tweet.get("text", "")}"</div>',
            unsafe_allow_html=True,
        )

        # Metrics display
        m1, m2 = st.columns(2)
        m1.markdown(f"**AI Category Tag:** <span class='{badge_class}'>{cat}</span>", unsafe_allow_html=True)
        m2.metric(label="AI Model Confidence", value=conf_pct)

    # Right Column: Enforcement Controls
    with col_right:
        st.subheader("⚡ Enforcement Controls")
        st.write("Execute moderation action based on severity verdict:")

        # Action 1: Clean / No Action
        if st.button("🟢 Approve / Clean (no_action)", use_container_width=True, type="secondary"):
            if send_moderation_action(active_tweet["id"], mod_id, "clean", "no_action"):
                st.rerun()

        # Action 2: Mild Hate / Warning
        if st.button("🟡 Warning Reply (warning_reply)", use_container_width=True, type="secondary"):
            if send_moderation_action(active_tweet["id"], mod_id, "mild_hate", "warning_reply"):
                st.rerun()

        # Action 3: Hate Speech / Delete
        if st.button("🟠 Delete Post (delete)", use_container_width=True, type="secondary"):
            if send_moderation_action(active_tweet["id"], mod_id, "hate_speech", "delete"):
                st.rerun()

        # Action 4: Severe Threat / Delete & Strike
        if st.button("🔴 Delete + Issue Strike (delete_and_strike)", use_container_width=True, type="primary"):
            if send_moderation_action(active_tweet["id"], mod_id, "severe_threat", "delete_and_strike"):
                st.rerun()
