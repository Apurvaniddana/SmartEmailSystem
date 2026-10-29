
import json
import os
import pandas as pd
import streamlit as st

# ============================================================
# SMART EMAIL SYSTEM - PROFESSIONAL STREAMLIT WEBSITE
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "email_history.json")
SUBSCRIPTION_FILE = os.path.join(DATA_DIR, "subscriptions.json")

st.set_page_config(
    page_title="Smart Email System",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# PROFESSIONAL UI / UX
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #f5f7fb;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    section[data-testid="stSidebar"] {
        background: #101828;
    }

    section[data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    .brand {
        font-size: 1.45rem;
        font-weight: 800;
        color: white;
        margin-bottom: 2px;
    }

    .brand-sub {
        color: #98a2b3;
        font-size: 0.78rem;
    }

    .hero {
        background: linear-gradient(135deg, #101828, #1d4ed8);
        border-radius: 24px;
        padding: 32px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 12px 30px rgba(16, 24, 40, 0.16);
    }

    .hero h1 {
        margin: 0;
        font-size: 2.35rem;
        font-weight: 800;
        letter-spacing: -1px;
    }

    .hero p {
        margin-top: 8px;
        color: #dbeafe;
        font-size: 1rem;
    }

    .status {
        display: inline-block;
        margin-top: 16px;
        padding: 7px 13px;
        border-radius: 999px;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.2);
        font-size: 0.8rem;
    }

    .card {
        background: white;
        border: 1px solid #e4e7ec;
        border-radius: 18px;
        padding: 20px;
        min-height: 125px;
        box-shadow: 0 5px 18px rgba(16, 24, 40, 0.05);
    }

    .card-label {
        color: #667085;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.4px;
    }

    .card-value {
        color: #101828;
        font-size: 2rem;
        font-weight: 800;
        margin-top: 7px;
    }

    .card-note {
        color: #98a2b3;
        font-size: 0.76rem;
        margin-top: 5px;
    }

    .section-title {
        color: #101828;
        font-size: 1.3rem;
        font-weight: 800;
        margin: 28px 0 12px;
    }

    .info-card {
        background: white;
        border: 1px solid #e4e7ec;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 5px 18px rgba(16, 24, 40, 0.04);
    }

    .info-label {
        color: #667085;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .info-value {
        color: #101828;
        font-size: 1.55rem;
        font-weight: 800;
        margin-top: 5px;
    }

    .info-text {
        color: #667085;
        font-size: 0.8rem;
        margin-top: 4px;
    }

    .architecture {
        background: white;
        border: 1px solid #e4e7ec;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 5px 18px rgba(16, 24, 40, 0.04);
    }

    .arch-step {
        background: #f8fafc;
        border: 1px solid #e4e7ec;
        border-radius: 12px;
        padding: 13px;
        text-align: center;
        margin: 7px 0;
        font-weight: 650;
        color: #344054;
    }

    .arch-arrow {
        text-align: center;
        color: #2563eb;
        font-size: 1.2rem;
    }

    .footer {
        text-align: center;
        color: #98a2b3;
        font-size: 0.78rem;
        padding-top: 20px;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA
# ============================================================

def load_json(path):
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def text(value):
    return "" if value is None else str(value)


history = load_json(HISTORY_FILE)
subscriptions = load_json(SUBSCRIPTION_FILE)

total = len(history)
ham = sum(
    1 for x in history
    if text(x.get("final_prediction")).upper() == "HAM"
)
spam = sum(
    1 for x in history
    if text(x.get("final_prediction")).upper() == "SPAM"
)
uncertain = sum(
    1 for x in history
    if text(x.get("final_prediction")).upper() == "UNCERTAIN"
)

spam_percentage = (spam / total * 100) if total else 0
ham_percentage = (ham / total * 100) if total else 0
uncertain_percentage = (uncertain / total * 100) if total else 0

unsubscribe_count = sum(
    1 for x in subscriptions if x.get("unsubscribe_url")
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        '<div class="brand">✉️ Smart Email</div>'
        '<div class="brand-sub">Email Security & Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Email History",
            "Subscriptions",
            "System Architecture",
        ],
    )

    st.divider()

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    st.markdown("### System Status")
    st.success("System Online")

    st.caption(f"Processed emails: {total}")
    st.caption(f"Subscriptions: {len(subscriptions)}")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>Smart Email System</h1>
        <p>
            Machine-learning based spam detection and intelligent
            subscription management for Gmail.
        </p>
        <div class="status">● Gmail Intelligence System Online</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    st.markdown(
        '<div class="section-title">Email Security Overview</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    cards = [
        ("TOTAL EMAILS", total, "Processed Gmail emails"),
        ("HAM EMAILS", ham, f"{ham_percentage:.2f}% of emails"),
        ("SPAM EMAILS", spam, f"{spam_percentage:.2f}% spam rate"),
        ("UNCERTAIN", uncertain, "Needs additional confidence"),
    ]

    for column, (label, value, note) in zip(
        [c1, c2, c3, c4], cards
    ):
        with column:
            st.markdown(
                f"""
                <div class="card">
                    <div class="card-label">{label}</div>
                    <div class="card-value">{value}</div>
                    <div class="card-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="section-title">Detection Analytics</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.35, 1])

    chart = pd.DataFrame(
        {
            "Category": ["Ham", "Spam", "Uncertain"],
            "Count": [ham, spam, uncertain],
        }
    )

    with left:
        st.markdown("#### Classification Volume")
        if total:
            st.bar_chart(
                chart.set_index("Category"),
                height=340,
            )
        else:
            st.info("No classification data available.")

    with right:
        st.markdown("#### Classification Distribution")
        if total:
            st.dataframe(
                chart.assign(
                    Percentage=[
                        f"{ham_percentage:.2f}%",
                        f"{spam_percentage:.2f}%",
                        f"{uncertain_percentage:.2f}%",
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Run the Gmail classifier to populate this section.")

    st.markdown(
        '<div class="section-title">Key Security Metrics</div>',
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)

    with m1:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-label">SPAM DETECTION RATE</div>
                <div class="info-value">{spam_percentage:.2f}%</div>
                <div class="info-text">
                    Percentage of processed emails classified as spam.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-label">SUBSCRIPTIONS TRACKED</div>
                <div class="info-value">{len(subscriptions)}</div>
                <div class="info-text">
                    Newsletter and subscription sources detected.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="info-label">UNSUBSCRIBE LINKS</div>
                <div class="info-value">{unsubscribe_count}</div>
                <div class="info-text">
                    Subscriptions with an available unsubscribe URL.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="section-title">Recent Email Activity</div>',
        unsafe_allow_html=True,
    )

    if history:
        rows = []

        for item in reversed(history[:15]):
            rows.append(
                {
                    "Sender": text(item.get("sender")),
                    "Subject": text(item.get("subject"))[:70],
                    "ML Result": text(item.get("ml_prediction")),
                    "Confidence": (
                        f"{text(item.get('confidence'))}%"
                        if item.get("confidence") != ""
                        else ""
                    ),
                    "Final Result": text(item.get("final_prediction")),
                    "Action": text(item.get("gmail_action")),
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "No email history found. Run gmail_classifier.py first."
        )


# ============================================================
# EMAIL HISTORY
# ============================================================

elif page == "Email History":

    st.markdown(
        '<div class="section-title">Email History & Analysis</div>',
        unsafe_allow_html=True,
    )

    if not history:
        st.warning("No email history found.")
    else:
        search = st.text_input(
            "🔎 Search",
            placeholder="Search sender, subject, prediction, or action...",
        )

        result_filter = st.selectbox(
            "Classification",
            ["All", "HAM", "SPAM", "UNCERTAIN"],
        )

        rows = []

        for item in history:
            row = {
                "Message ID": text(item.get("message_id")),
                "Sender": text(item.get("sender")),
                "Subject": text(item.get("subject")),
                "Date": text(item.get("date")),
                "ML Prediction": text(item.get("ml_prediction")),
                "ML Score": text(item.get("ml_score")),
                "Confidence": text(item.get("confidence")),
                "Final Result": text(item.get("final_prediction")),
                "Gmail Action": text(item.get("gmail_action")),
            }

            searchable = " ".join(row.values()).lower()

            if search and search.lower() not in searchable:
                continue

            if (
                result_filter != "All"
                and row["Final Result"].upper() != result_filter
            ):
                continue

            rows.append(row)

        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(f"{len(rows)} matching records")
        else:
            st.info("No matching email records.")


# ============================================================
# SUBSCRIPTIONS
# ============================================================

elif page == "Subscriptions":

    st.markdown(
        '<div class="section-title">Subscription Intelligence</div>',
        unsafe_allow_html=True,
    )

    s1, s2, s3 = st.columns(3)

    s1.metric("Subscriptions", len(subscriptions))
    s2.metric("Unsubscribe Available", unsubscribe_count)
    s3.metric(
        "No Unsubscribe URL",
        len(subscriptions) - unsubscribe_count,
    )

    if subscriptions:
        rows = []

        for item in subscriptions:
            rows.append(
                {
                    "Sender": text(item.get("sender")),
                    "Email": text(item.get("sender_email")),
                    "Type": text(item.get("type")),
                    "Subject": text(item.get("subject")),
                    "Status": text(item.get("status")),
                    "Unsubscribe URL": text(
                        item.get("unsubscribe_url")
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No subscriptions found.")


# ============================================================
# SYSTEM ARCHITECTURE
# ============================================================

elif page == "System Architecture":

    st.markdown(
        '<div class="section-title">System Architecture</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="architecture">
            <div class="arch-step">📩 Gmail API</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-step">📨 Email Reader</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-step">🧹 Text Preprocessing</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-step">🔢 TF-IDF Feature Extraction</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-step">🤖 Machine Learning Classifier</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-step">🛡️ Rule-Based Spam Analysis</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-step">⚖️ Hybrid Decision Engine</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-step">📬 Subscription Detection</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-step">🗂️ Email History & Subscription Storage</div>
            <div class="arch-arrow">↓</div>
            <div class="arch-step">📊 Streamlit Dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">Technologies Used</div>',
        unsafe_allow_html=True,
    )

    technology_data = pd.DataFrame(
        {
            "Technology": [
                "Python",
                "Gmail API",
                "Scikit-learn / Machine Learning",
                "TF-IDF",
                "Pandas",
                "JSON",
                "Streamlit",
            ],
            "Role in Project": [
                "Core application development",
                "Gmail integration and email retrieval",
                "Spam / ham classification",
                "Convert email text into numerical features",
                "Data processing and dashboard tables",
                "Store email history and subscriptions",
                "Professional web dashboard",
            ],
        }
    )

    st.dataframe(
        technology_data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        Smart Email System • Machine Learning Based Spam Detection •
        Gmail Integration • Subscription Management
    </div>
    """,
    unsafe_allow_html=True,
)
