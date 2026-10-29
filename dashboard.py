import streamlit as st
import os
import json
import pickle
import re
import csv
import html
import hashlib
import hmac
import secrets
import shutil
import time
from datetime import datetime
from email_system.subscription_manager import load_subscriptions

from pathlib import Path
import streamlit as st


def load_ui_styles():
    css_path = Path(__file__).with_name("ui_styles.css")

    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True
        )

# Dashboard update placeholder

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart Email System",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "saved_model"
)

HISTORY_FILE = os.path.join(
    DATA_DIR,
    "email_history.json"
)

SUBSCRIPTIONS_FILE = os.path.join(
    DATA_DIR,
    "subscriptions.json"
)

USERS_FILE = os.path.join(
    DATA_DIR,
    "users.json"
)

GOOGLE_OAUTH_CLIENT_FILE = os.path.join(BASE_DIR, "google_oauth_client.json")
GOOGLE_TOKEN_DIR = os.path.join(DATA_DIR, "google_tokens")
GOOGLE_OAUTH_STATES_FILE = os.path.join(DATA_DIR, "google_oauth_states.json")
USER_DATA_DIR = os.path.join(DATA_DIR, "users")
LEGACY_OWNER_FILE = os.path.join(DATA_DIR, "legacy_data_owner.json")
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.modify",
]
GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI", "http://localhost:8501"
)

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "improved_linear_svc.pkl"
)

VECTORIZER_FILE = os.path.join(
    MODEL_DIR,
    "improved_tfidf_vectorizer.pkl"
)


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# THEME TOKENS / CSS
# ============================================================
# Unified token-driven stylesheet is injected after the sidebar theme toggle.


# ============================================================
# SESSION STATE
# ============================================================

if "gmail_results" not in st.session_state:
    st.session_state.gmail_results = []

if "selected_subscriptions" not in st.session_state:
    st.session_state.selected_subscriptions = set()


# ============================================================
# JSON HELPER
# ============================================================

def load_json_file(file_path, default_value):

    try:

        if not os.path.exists(file_path):
            return default_value

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data

    except Exception:
        return default_value


# ============================================================
# SAVE JSON FILE
# ============================================================

def save_json_file(file_path, data):

    try:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

        return True

    except Exception:
        return False


# ============================================================
# EMAIL HISTORY
# ============================================================

def load_history():

    data = load_json_file(
        HISTORY_FILE,
        []
    )

    if isinstance(data, list):
        return data

    return []
def calculate_security_statistics(history):

    total = len(history)

    spam = 0
    ham = 0
    uncertain = 0

    for email in history:

        prediction = str(
            email.get(
                "final_prediction",
                ""
            )
        ).upper()

        if prediction == "SPAM":
            spam += 1

        elif prediction == "HAM":
            ham += 1

        elif prediction == "UNCERTAIN":
            uncertain += 1

    spam_rate = (
        (spam / total) * 100
        if total > 0
        else 0
    )

    return {
        "total": total,
        "spam": spam,
        "ham": ham,
        "uncertain": uncertain,
        "spam_rate": spam_rate
    }

# ============================================================
# SUBSCRIPTIONS
# ============================================================

def load_subscriptions():

    data = load_json_file(
        SUBSCRIPTIONS_FILE,
        []
    )

    if isinstance(data, list):
        return data

    return []


# ============================================================
# LOAD ML MODEL
# ============================================================

@st.cache_resource
def load_ml_model():

    if not os.path.exists(MODEL_FILE):

        return (
            None,
            None,
            "ML model file not found: "
            + MODEL_FILE
        )

    if not os.path.exists(VECTORIZER_FILE):

        return (
            None,
            None,
            "TF-IDF vectorizer file not found: "
            + VECTORIZER_FILE
        )

    try:

        with open(
            MODEL_FILE,
            "rb"
        ) as file:

            model = pickle.load(file)

        with open(
            VECTORIZER_FILE,
            "rb"
        ) as file:

            vectorizer = pickle.load(file)

        return (
            model,
            vectorizer,
            None
        )

    except Exception as error:

        return (
            None,
            None,
            str(error)
        )


model, vectorizer, model_error = load_ml_model()


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = str(text)

    # Remove HTTP/HTTPS URLs
    text = re.sub(
        r"https?://\S+",
        " ",
        text
    )

    # Remove www URLs
    text = re.sub(
        r"www\.\S+",
        " ",
        text
    )

    # Remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def clean_email_body(body):
    """Normalize a fetched email body without removing URLs or HTML.

    URLs are retained because the phishing checks need to inspect them.
    HTML is retained for the email display renderer.
    """
    if body is None:
        return ""
    return str(body).strip()


# ============================================================
# RULE BASED ANALYSIS
# ============================================================

def rule_analysis(
    sender,
    subject,
    body
):

    text = (
        str(subject)
        + " "
        + str(body)
    ).lower()

    # Initialize BEFORE using them
    score = 0
    indicators = []

    # --------------------------------------------------------
    # URL ANALYSIS
    # --------------------------------------------------------

    urls = re.findall(
        r"https?://[^\s]+|www\.[^\s]+",
        text
    )

    if urls:

        indicators.append(
            "url_present"
        )

    # --------------------------------------------------------
    # SHORTENED URL CHECK
    # --------------------------------------------------------

    shortened_domains = [
        "bit.ly",
        "tinyurl.com",
        "t.co",
        "goo.gl",
        "is.gd",
        "ow.ly"
    ]

    for url in urls:

        if any(
            domain in url
            for domain in shortened_domains
        ):

            indicators.append(
                "shortened_url"
            )

            score += 3

            break

    # --------------------------------------------------------
    # SUSPICIOUS URL KEYWORDS
    # --------------------------------------------------------

    suspicious_url_words = [
        "verify",
        "login",
        "password",
        "account",
        "secure",
        "claim",
        "update"
    ]

    for url in urls:

        if any(
            word in url.lower()
            for word in suspicious_url_words
        ):

            indicators.append(
                "suspicious_url"
            )

            score += 2

            break

    # --------------------------------------------------------
    # TRUSTED SENDERS
    # --------------------------------------------------------

    trusted_domains = [

        "@linkedin.com",

        "@16personalities.com",

        "@emertxe.com",

        "@ieee.org",

        "@deliver.ieee.org",

        "@unstop.news",

        "@napkin.ai",

        "@webex.com",

        "@zoom.us",

        "@google.com",

        "@tatatechnologies.com",

        "@hpe.com",

        "@leetcode.com",

        "@olympics.com",

        "@mailer.olympics.com"
    ]

    sender_lower = str(
        sender
    ).lower()

    trusted_sender = any(
        domain in sender_lower
        for domain in trusted_domains
    )

    # --------------------------------------------------------
    # SPAM KEYWORD RULES
    # --------------------------------------------------------

    spam_rules = [

        (r"\bfree\b", 1),

        (r"\boffer\b", 2),

        (r"\bbonus\b", 2),

        (r"\bdeal\b", 2),

        (r"\bdiscount\b", 2),

        (r"\bpromotion\b", 1),

        (r"\bprize\b", 3),

        (r"\breward\b", 3),

        (r"\bwon\b", 4),

        (r"\bwinner\b", 4),

        (r"\blottery\b", 5),

        (r"\bcash prize\b", 5),

        (r"\bclaim your prize\b", 6),

        (r"\bclaim your money\b", 6),

        (r"\bclick here to claim\b", 6),

        (r"\bverify your password\b", 6),

        (r"\baccount suspended\b", 6),

        (r"\burgent\b", 3)
    ]

    for pattern, points in spam_rules:

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):

            score += points

            indicator_name = pattern

            # Convert regex indicator to readable text
            indicator_name = (
                indicator_name
                .replace(r"\b", "")
            )

            indicators.append(
                indicator_name
            )

    # --------------------------------------------------------
    # EXCESSIVE EXCLAMATION MARKS
    # --------------------------------------------------------

    if text.count("!") >= 5:

        score += 2

        indicators.append(
            "excessive_exclamation"
        )

    # --------------------------------------------------------
    # MONEY AMOUNT
    # --------------------------------------------------------

    money_pattern = r"[$₹€£]\s?\d+"

    if re.search(
        money_pattern,
        text
    ):

        score += 2

        indicators.append(
            "money_amount"
        )

    return (
        trusted_sender,
        score,
        indicators
    )


# ============================================================
# PHISHING / URL SECURITY ANALYSIS
# ============================================================

def analyze_phishing_risk(sender, subject, body):
    """Heuristic phishing assessment; this is a warning aid, not a guarantee."""
    from urllib.parse import urlsplit

    sender_text = str(sender or "")
    subject_text = str(subject or "")
    body_text = str(body or "")
    combined_text = f"{subject_text} {body_text}"
    combined_lower = combined_text.casefold()

    # Extract plain-text URLs and HTML href destinations.
    plain_urls = re.findall(
        r"https?://[^\s<>\"']+|www\.[^\s<>\"']+",
        combined_text,
        re.IGNORECASE,
    )
    href_urls = re.findall(
        r"(?is)\bhref\s*=\s*[\"']([^\"']+)[\"']",
        body_text,
    )
    urls = []
    for raw_url in plain_urls + href_urls:
        url = html.unescape(str(raw_url)).strip().rstrip(".,!?;:)]}")
        if url and url not in urls and url.casefold().startswith(("http://", "https://", "www.")):
            urls.append(url)

    reasons = []
    suspicious_urls = []
    score = 0

    shortened_domains = {
        "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd",
        "ow.ly", "buff.ly", "cutt.ly", "shorturl.at",
    }
    suspicious_url_words = {
        "login", "verify", "verification", "password", "account",
        "secure", "security", "signin", "sign-in", "update",
        "confirm", "unlock", "suspended", "wallet", "payment",
    }
    suspicious_tlds = {".xyz", ".top", ".click", ".buzz", ".support"}

    def host_from_url(raw_url):
        candidate = raw_url if raw_url.casefold().startswith(("http://", "https://")) else "http://" + raw_url
        try:
            return (urlsplit(candidate).hostname or "").casefold().strip(".")
        except ValueError:
            return ""

    sender_match = re.search(r"([A-Z0-9._%+\-]+)@([A-Z0-9.\-]+\.[A-Z]{2,})", sender_text, re.I)
    sender_domain = sender_match.group(2).casefold().strip(".") if sender_match else ""

    def add_reason(message, points=0, url=None):
        nonlocal score
        score += points
        if message not in reasons:
            reasons.append(message)
        if url and url not in suspicious_urls:
            suspicious_urls.append(url)

    # URL-level signals.
    for url in urls:
        host = host_from_url(url)
        normalized = url if url.casefold().startswith(("http://", "https://")) else "http://" + url
        try:
            authority = urlsplit(normalized).netloc.casefold()
        except ValueError:
            authority = ""
        url_reasons = []

        if "@" in authority:
            url_reasons.append(("URL contains an @ symbol that may obscure its true destination.", 3))
        if normalized.casefold().startswith("http://"):
            url_reasons.append(("URL uses HTTP rather than encrypted HTTPS.", 1))
        if host.startswith("xn--") or ".xn--" in host:
            url_reasons.append(("URL uses a punycode domain that may resemble another domain.", 3))
        if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
            url_reasons.append(("URL points directly to an IP address instead of a domain name.", 3))
        if host in shortened_domains or any(host.endswith("." + domain) for domain in shortened_domains):
            url_reasons.append(("URL uses a shortened-link service that can hide its final destination.", 2))
        if any(word in host for word in suspicious_url_words):
            url_reasons.append(("URL domain contains account, login, or security-related wording.", 2))
        if any(host.endswith(tld) for tld in suspicious_tlds):
            url_reasons.append(("URL uses a domain extension that warrants extra scrutiny.", 2))
        if sender_domain and host and not (
            host == sender_domain
            or host.endswith("." + sender_domain)
            or sender_domain.endswith("." + host)
        ):
            url_reasons.append(("Link domain differs from the sender's domain; verify the destination.", 1))

        for reason, points in url_reasons:
            add_reason(reason, points, url=url)

    # Detect anchor text that claims to be a different domain from its href.
    for anchor_match in re.finditer(
        r"(?is)<a\b[^>]*\bhref\s*=\s*[\"']([^\"']+)[\"'][^>]*>(.*?)</a\s*>",
        body_text,
    ):
        href = html.unescape(anchor_match.group(1)).strip()
        anchor_text = re.sub(r"<[^>]+>", " ", anchor_match.group(2))
        anchor_text = html.unescape(anchor_text).strip()
        displayed_host = host_from_url(anchor_text) if re.match(r"(?i)^(https?://|www\.)", anchor_text) else ""
        destination_host = host_from_url(href)
        if displayed_host and destination_host and displayed_host != destination_host:
            add_reason(
                f"Displayed link text points to {displayed_host}, but the actual destination is {destination_host}.",
                5,
                url=href,
            )

    # Sender display-name impersonation checks. These are heuristics only.
    brand_domains = {
        "paypal": ("paypal.com",),
        "google": ("google.com", "googlemail.com"),
        "microsoft": ("microsoft.com", "microsoftonline.com"),
        "apple": ("apple.com",),
        "amazon": ("amazon.com", "amazon.in"),
        "netflix": ("netflix.com",),
        "linkedin": ("linkedin.com",),
        "facebook": ("facebook.com", "fb.com"),
        "instagram": ("instagram.com",),
    }
    display_name = sender_text.split("<", 1)[0].strip().strip('"').casefold()
    for brand, allowed_domains in brand_domains.items():
        if brand in display_name and sender_domain and not any(
            sender_domain == domain or sender_domain.endswith("." + domain)
            for domain in allowed_domains
        ):
            add_reason(
                f"Sender display name mentions {brand.title()}, but the sender address uses a different domain.",
                4,
            )
            break

    # Urgent/threatening language commonly used to pressure recipients.
    urgency_patterns = [
        r"\baccount\s+(?:will be|has been)\s+(?:suspended|closed|locked)\b",
        r"\bact\s+now\b",
        r"\bimmediate(?:ly)?\s+action\s+required\b",
        r"\bwithin\s+\d+\s+hours?\b",
        r"\blast\s+warning\b",
        r"\byour\s+account\s+will\s+be\s+closed\b",
        r"\bunusual\s+activity\s+(?:detected|on your account)\b",
        r"\bverify\s+your\s+account\s+(?:now|immediately|today)\b",
    ]
    if any(re.search(pattern, combined_lower) for pattern in urgency_patterns):
        add_reason("Message uses urgent or threatening language that may pressure the recipient to act quickly.", 2)

    # Requests for credentials or one-time codes.
    sensitive_request_patterns = [
        r"\b(?:send|share|provide|enter|confirm)\s+(?:me\s+)?(?:your\s+)?(?:password|passcode|otp|one[- ]time code|verification code)\b",
        r"\b(?:password|otp|one[- ]time code|verification code)\s+(?:is\s+required|to verify|to unlock)\b",
        r"\bclick\s+(?:the\s+)?link\s+to\s+(?:verify|reset|confirm)\s+your\s+(?:password|account)\b",
        r"\b(?:bank details|credit card details|social security number)\b",
    ]
    if any(re.search(pattern, combined_lower) for pattern in sensitive_request_patterns):
        add_reason("Message appears to request credentials, verification codes, or sensitive personal/financial information.", 5)

    if not urls:
        reasons.append("No web links were detected in the email.")

    if score >= 7:
        risk_level = "HIGH"
    elif score >= 3:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_level": risk_level,
        "score": score,
        "urls": urls,
        "suspicious_urls": suspicious_urls,
        "reasons": list(dict.fromkeys(reasons)),
    }


# ============================================================
# SUBSCRIPTION DETECTION
# ============================================================

# ============================================================
# DETECT EMAIL SUBSCRIPTIONS
# ============================================================

def detect_subscription(
    sender,
    subject,
    body
):

    text = (
        str(sender)
        + " "
        + str(subject)
        + " "
        + str(body)
    ).lower()

    indicators = []

    # --------------------------------------------------------
    # SUBSCRIPTION KEYWORDS
    # --------------------------------------------------------

    subscription_keywords = [
        "unsubscribe",
        "newsletter",
        "subscription",
        "subscribed",
        "manage preferences",
        "email preferences",
        "mailing list",
        "weekly update",
        "monthly update",
        "promotional emails",
        "marketing emails"
    ]

    for keyword in subscription_keywords:

        if keyword in text:

            indicators.append(
                "Subscription indicator: "
                + keyword
            )

    # --------------------------------------------------------
    # NO SUBSCRIPTION DETECTED
    # --------------------------------------------------------

    if not indicators:

        return None

    # --------------------------------------------------------
    # DETERMINE SUBSCRIPTION TYPE
    # --------------------------------------------------------

    if (
        "newsletter" in text
        or "weekly update" in text
        or "monthly update" in text
    ):

        subscription_type = "Newsletter"

    elif (
        "promotional emails" in text
        or "marketing emails" in text
    ):

        subscription_type = "Promotional"

    elif (
        "subscription" in text
        or "subscribed" in text
        or "mailing list" in text
    ):

        subscription_type = "Subscription"

    else:

        subscription_type = "Email Subscription"
    # --------------------------------------------------------
    # FIND UNSUBSCRIBE URL
    # --------------------------------------------------------

    import re

    unsubscribe_url = None

    url_pattern = r'https?://[^\s<>"\']+'

    urls = re.findall(
        url_pattern,
        str(body or "")
    )

    for url in urls:

        if (
            "unsubscribe" in url.lower()
            or "preferences" in url.lower()
            or "optout" in url.lower()
        ):

            unsubscribe_url = url

            break

    # --------------------------------------------------------
    # RETURN SUBSCRIPTION INFORMATION
    # --------------------------------------------------------

    return {
        "type": subscription_type,
        "unsubscribe_url": unsubscribe_url,
        "indicators": indicators
    }

# ============================================================
# RESCAN EMAIL HISTORY FOR SUBSCRIPTIONS
# ============================================================

def rescan_subscriptions_from_history():

    history = load_history()

    detected_count = 0

    try:

        from email_system.subscription_manager import (
            add_subscription
        )

    except ImportError:

        return 0

    for item in history:

        sender = item.get(
            "sender",
            ""
        )

        subject = item.get(
            "subject",
            ""
        )

        body = item.get(
            "body",
            ""
        )

        subscription_info = detect_subscription(
            sender,
            subject,
            body
        )

        if subscription_info:

            try:

                add_subscription(
                    sender=sender,
                    subject=subject,
                    subscription_type=subscription_info.get(
                        "type",
                        "Email Subscription"
                    ),
                    unsubscribe_url=subscription_info.get(
                        "unsubscribe_url"
                    ),
                    indicators=subscription_info.get(
                        "indicators",
                        []
                    )
                )

                detected_count += 1

            except Exception:

                pass

    return detected_count


# ============================================================
# CLASSIFY EMAIL USING ML
# ============================================================

def classify_email(
    subject,
    body
):

    if (
        model is None
        or vectorizer is None
    ):

        return (
            "ERROR",
            0.0
        )

    subject = clean_text(
        subject
    )

    body = clean_text(
        body
    )

    combined_text = (
        subject
        + " "
        + body
    ).strip()

    if not combined_text:

        return (
            "ERROR",
            0.0
        )

    try:

        features = vectorizer.transform(
            [combined_text]
        )

        prediction = model.predict(
            features
        )[0]

        # LinearSVC normally provides decision_function
        if hasattr(
            model,
            "decision_function"
        ):

            raw_score = model.decision_function(
                features
            )

            # Binary classification
            if hasattr(
                raw_score,
                "__len__"
            ):

                try:
                    decision_score = float(
                        raw_score[0]
                    )
                except Exception:
                    decision_score = float(
                        raw_score
                    )

            else:

                decision_score = float(
                    raw_score
                )

        else:

            decision_score = 1.0

        prediction_string = str(
            prediction
        ).lower()

        if prediction_string == "spam":

            final_prediction = "SPAM"

        elif prediction_string in [
            "ham",
            "not spam",
            "legitimate",
            "safe"
        ]:

            final_prediction = "HAM"

        else:

            # Handle numeric labels if model uses 0/1
            if prediction_string in [
                "1",
                "true"
            ]:

                final_prediction = "SPAM"

            else:

                final_prediction = "HAM"

        return (
            final_prediction,
            decision_score
        )

    except Exception:

        return (
            "ERROR",
            0.0
        )


# ============================================================
# HYBRID DECISION
# ============================================================

def hybrid_decision(
    ml_prediction,
    ml_score,
    sender,
    subject,
    body
):

    trusted_sender, rule_score, indicators = rule_analysis(
        sender,
        subject,
        body
    )

    text = (
        str(subject)
        + " "
        + str(body)
    ).lower()

    # --------------------------------------------------------
    # VERY STRONG SPAM PHRASES
    # --------------------------------------------------------

    very_strong_spam = [

        "you have won",

        "claim your prize",

        "claim your money",

        "lottery winner",

        "cash prize",

        "click here to claim",

        "verify your password",

        "account suspended"
    ]

    strong_spam = any(
        phrase in text
        for phrase in very_strong_spam
    )

    # --------------------------------------------------------
    # ML STRONG SPAM
    # --------------------------------------------------------

    if (
        ml_prediction == "SPAM"
        and ml_score >= 0.50
    ):

        return "SPAM"

    # --------------------------------------------------------
    # STRONG SPAM PHRASE
    # --------------------------------------------------------

    if strong_spam:

        if not trusted_sender:

            return "SPAM"

        if (
            trusted_sender
            and ml_prediction == "SPAM"
            and ml_score >= 0.10
        ):

            return "SPAM"

    # --------------------------------------------------------
    # TRUSTED SENDER + HAM
    # --------------------------------------------------------

    if (
        trusted_sender
        and ml_prediction == "HAM"
    ):

        return "HAM"

    # --------------------------------------------------------
    # STRONG HAM
    # --------------------------------------------------------

    if (
        ml_prediction == "HAM"
        and ml_score <= -0.20
    ):

        return "HAM"

    # --------------------------------------------------------
    # ML SPAM
    # --------------------------------------------------------

    if (
        ml_prediction == "SPAM"
        and ml_score >= 0.20
    ):

        return "SPAM"

    # --------------------------------------------------------
    # RULE BASED SPAM
    # --------------------------------------------------------

    if not trusted_sender:

        if rule_score >= 6:

            return "SPAM"

    # --------------------------------------------------------
    # WEAK HAM
    # --------------------------------------------------------

    if (
        ml_prediction == "HAM"
        and ml_score <= -0.10
    ):

        return "HAM"

    # --------------------------------------------------------
    # UNCERTAIN
    # --------------------------------------------------------

    return "UNCERTAIN"


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(score):

    try:

        score = float(score)

    except Exception:

        return 0.0

    confidence = 50 + (
        abs(score) * 50
    )

    confidence = min(
        confidence,
        99.99
    )

    return confidence


# ============================================================
# SMART EMAIL ANALYSIS
# ============================================================

def generate_smart_analysis(
    ml_prediction,
    ml_score,
    confidence,
    trusted_sender,
    rule_score,
    indicators,
    final_prediction
):

    reasons = []

    # --------------------------------------------------------
    # ML REASON
    # --------------------------------------------------------

    if ml_prediction == "SPAM":

        reasons.append(
            "Machine learning detected spam-like content."
        )

    elif ml_prediction == "HAM":

        reasons.append(
            "Machine learning did not detect strong spam patterns."
        )

    else:

        reasons.append(
            "Machine learning could not classify the email."
        )

    # --------------------------------------------------------
    # RULE BASED EXPLANATIONS
    # --------------------------------------------------------

    indicator_explanations = {

        "free":
            "Contains the word 'free'.",

        "offer":
            "Contains an offer-related word.",

        "bonus":
            "Contains a bonus-related word.",

        "deal":
            "Contains a deal-related word.",

        "discount":
            "Contains a discount-related word.",

        "promotion":
            "Contains promotional content.",

        "prize":
            "Mentions a prize.",

        "reward":
            "Mentions a reward.",

        "won":
            "Contains a winning-related message.",

        "winner":
            "Claims that the recipient is a winner.",

        "lottery":
            "Mentions a lottery.",

        "cash prize":
            "Mentions a cash prize.",

        "claim your prize":
            "Asks the user to claim a prize.",

        "claim your money":
            "Asks the user to claim money.",

        "click here to claim":
            "Uses a strong call-to-action to claim something.",

        "verify your password":
            "Requests password verification.",

        "account suspended":
            "Claims that an account has been suspended.",

        "urgent":
            "Uses urgent language.",

        "excessive_exclamation":
            "Contains an unusually high number of exclamation marks.",

        "money_amount":
            "Contains a monetary amount.",

        "url_present":
            "The email contains a web link.",

        "shortened_url":
            "The email contains a shortened URL, which can hide the actual destination.",

        "suspicious_url":
            "The URL contains words commonly associated with account verification or login requests."
    }

    for indicator in indicators:

        explanation = indicator_explanations.get(
            indicator,
            f"Spam indicator detected: {indicator}"
        )

        if explanation not in reasons:

            reasons.append(
                explanation
            )

    # --------------------------------------------------------
    # SENDER ANALYSIS
    # --------------------------------------------------------

    if trusted_sender:

        reasons.append(
            "The sender belongs to a trusted domain."
        )

    else:

        reasons.append(
            "The sender is not in the trusted sender list."
        )

    # --------------------------------------------------------
    # RULE SCORE
    # --------------------------------------------------------

    if rule_score >= 6:

        reasons.append(
            f"Rule-based analysis produced a high spam score of {rule_score}."
        )

    elif rule_score > 0:

        reasons.append(
            f"Rule-based analysis detected spam indicators with a score of {rule_score}."
        )

    # --------------------------------------------------------
    # FINAL RISK
    # --------------------------------------------------------

    if final_prediction == "SPAM":

        risk_level = "HIGH"

        recommendation = (
            "Treat this email as suspicious. "
            "Avoid clicking links or providing personal information."
        )

    elif final_prediction == "HAM":

        risk_level = "LOW"

        recommendation = (
            "This email appears to be legitimate based on "
            "the current ML and rule-based analysis."
        )

    else:

        risk_level = "MEDIUM"

        recommendation = (
            "The result is uncertain. Review the sender "
            "and email content carefully before taking action."
        )

    return {

        "risk_level":
            risk_level,

        "reasons":
            reasons,

        "recommendation":
            recommendation,

        "ml_prediction":
            ml_prediction,

        "ml_score":
            ml_score,

        "confidence":
            confidence,

        "trusted_sender":
            trusted_sender,

        "rule_score":
            rule_score,

        "final_prediction":
            final_prediction
    }


# ============================================================
# SAVE ANALYZED EMAIL TO HISTORY
# ============================================================

def save_email_history(item):

    history = load_history()

    message_id = item.get(
        "message_id",
        ""
    )

    if not message_id:

        return False

    # Prevent duplicate emails
    for existing in history:

        if existing.get(
            "message_id"
        ) == message_id:

            return False

    record = {

        "message_id":
            item.get(
                "message_id",
                ""
            ),

        "sender":
            item.get(
                "sender",
                ""
            ),

        "subject":
            item.get(
                "subject",
                ""
            ),

        "body":
            item.get(
                "body",
                ""
            ),
        "date":
            item.get(
                "date",
                ""
            ),

        "ml_prediction":
            item.get(
                "ml_prediction",
                ""
            ),

        "ml_score":
            item.get(
                "ml_score",
                0
            ),

        "confidence":
            item.get(
                "confidence",
                0
            ),

        "trusted_sender":
            item.get(
                "trusted_sender",
                False
            ),

        "rule_score":
            item.get(
                "rule_score",
                0
            ),

        "indicators":
            item.get(
                "indicators",
                []
            ),

        "phishing_risk":
            item.get(
                "phishing_risk",
                "LOW"
            ),

        "phishing_score":
            item.get(
                "phishing_score",
                0
            ),

        "suspicious_urls":
            item.get(
                "suspicious_urls",
                []
            ),

        "phishing_reasons":
            item.get(
                "phishing_reasons",
                []
            ),

        "final_prediction":
            item.get(
                "final_prediction",
                ""
            ),

        "gmail_action":
            item.get(
                "gmail_action",
                "ANALYZED"
            ),

        "timestamp":
            datetime.now().isoformat()
    }

    history.append(record)

    return save_json_file(
        HISTORY_FILE,
        history
    )


# ============================================================
# REFRESH PHISHING SCORES IN EMAIL HISTORY
# ============================================================

def refresh_phishing_scores_in_history():

    history = load_history()
    changed = False

    for item in history:

        # Recalculate every stored email once so older history
        # records also receive the phishing analysis.
        analysis = analyze_phishing_risk(
            item.get("sender", ""),
            item.get("subject", ""),
            item.get("body", "")
        )

        new_risk = analysis.get("risk_level", "LOW")
        new_score = analysis.get("score", 0)
        new_urls = analysis.get("suspicious_urls", [])
        new_reasons = analysis.get("reasons", [])

        if (
            item.get("phishing_risk") != new_risk
            or item.get("phishing_score") != new_score
            or item.get("suspicious_urls", []) != new_urls
            or item.get("phishing_reasons", []) != new_reasons
        ):
            item["phishing_risk"] = new_risk
            item["phishing_score"] = new_score
            item["suspicious_urls"] = new_urls
            item["phishing_reasons"] = new_reasons
            changed = True

    if changed:

        save_json_file(
            HISTORY_FILE,
            history
        )

    return changed


# ============================================================
# GMAIL SERVICE
# ============================================================

def get_gmail_service():
    """Build Gmail API service using the currently signed-in Google account."""
    google_sub = st.session_state.get("google_user_sub")
    if not google_sub:
        return None

    token_file = os.path.join(
        GOOGLE_TOKEN_DIR,
        hashlib.sha256(google_sub.encode("utf-8")).hexdigest() + ".json",
    )
    if not os.path.exists(token_file):
        return None

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        credentials = Credentials.from_authorized_user_file(
            token_file, GOOGLE_SCOPES
        )
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            with open(token_file, "w", encoding="utf-8") as token_out:
                token_out.write(credentials.to_json())
        if not credentials or not credentials.valid:
            return None
        return build("gmail", "v1", credentials=credentials, cache_discovery=False)
    except Exception as error:
        print(f"Could not create Gmail service for signed-in account: {error}")
        return None


# ============================================================
# GET GMAIL HEADER
# ============================================================

def get_gmail_header(
    headers,
    name
):

    for header in headers:

        if header.get(
            "name",
            ""
        ).lower() == name.lower():

            return header.get(
                "value",
                ""
            )

    return ""

# ============================================================
# GET ALREADY ANALYZED EMAIL IDS
# ============================================================

def get_processed_message_ids():

    history = load_history()

    return {
        str(item.get("message_id"))
        for item in history
        if item.get("message_id")
    }
# ============================================================
# ANALYZE GMAIL EMAILS
# ============================================================


def execute_gmail_request(request, max_attempts=7):
    """Retry temporary Gmail quota and server errors with exponential backoff."""
    import time

    for attempt in range(max_attempts):
        try:
            return request.execute()
        except Exception as error:
            message = str(error).lower()
            retryable = any(term in message for term in (
                "ratelimitexceeded",
                "userratelimitexceeded",
                "quota exceeded",
                "429",
                "500",
                "502",
                "503",
                "504",
                "backenderror",
            ))

            if not retryable or attempt == max_attempts - 1:
                raise

            delay = min(2 ** attempt, 32)
            print(f"Gmail temporary error. Retrying in {delay} seconds...")
            time.sleep(delay)


def analyze_gmail_emails(max_results=20, scan_all=False):
    """Analyze recent Gmail messages or paginate through the full inbox.
    Each result is saved immediately so an interrupted scan keeps its progress.
    """
    try:
        from email_system.gmail_classifier import (
            get_header,
            extract_body
        )

        service = get_gmail_service()
        if service is None:
            return {"error": "Gmail service could not be created."}

        processed_ids = get_processed_message_ids()
        results = []
        page_token = None
        page_size = 25 if scan_all else min(int(max_results), 50)

        while True:
            request_kwargs = {
                "userId": "me",
                "labelIds": ["INBOX"],
                "maxResults": page_size
            }
            if page_token:
                request_kwargs["pageToken"] = page_token

            response = execute_gmail_request(
                service.users().messages().list(**request_kwargs)
            )
            messages = response.get("messages", [])

            for message_info in messages:
                message_id = message_info.get("id")
                if not message_id or str(message_id) in processed_ids:
                    continue

                try:
                    message = execute_gmail_request(
                        service.users().messages().get(
                            userId="me",
                            id=message_id,
                            format="full"
                        )
                    )

                    payload = message.get("payload", {})
                    headers = payload.get("headers", [])

                    try:
                        sender = get_header(headers, "From")
                        subject = get_header(headers, "Subject")
                        date = get_header(headers, "Date")
                    except Exception:
                        sender = get_gmail_header(headers, "From")
                        subject = get_gmail_header(headers, "Subject")
                        date = get_gmail_header(headers, "Date")

                    body = clean_email_body(extract_body(payload) or "")

                    ml_prediction, ml_score = classify_email(subject, body)
                    trusted_sender, rule_score, indicators = rule_analysis(
                        sender, subject, body
                    )
                    final_prediction = hybrid_decision(
                        ml_prediction, ml_score, sender, subject, body
                    )
                    phishing_analysis = analyze_phishing_risk(
                        sender, subject, body
                    )

                    result = {
                        "message_id": message_id,
                        "sender": sender,
                        "subject": subject,
                        "body": body,
                        "date": date,
                        "ml_prediction": ml_prediction,
                        "ml_score": ml_score,
                        "confidence": calculate_confidence(ml_score),
                        "trusted_sender": trusted_sender,
                        "rule_score": rule_score,
                        "indicators": indicators,
                        "phishing_risk": phishing_analysis["risk_level"],
                        "phishing_score": phishing_analysis["score"],
                        "suspicious_urls": phishing_analysis["suspicious_urls"],
                        "phishing_reasons": phishing_analysis["reasons"],
                        "final_prediction": final_prediction,
                        "gmail_action": "ANALYZED",
                        "subscription_detected": False
                    }

                    try:
                        subscription_info = detect_subscription(
                            sender, subject, body
                        )
                        if subscription_info:
                            from email_system.subscription_manager import (
                                add_subscription
                            )
                            add_subscription(
                                sender=sender,
                                subject=subject,
                                subscription_type=subscription_info.get(
                                    "type", "Email Subscription"
                                ),
                                unsubscribe_url=subscription_info.get(
                                    "unsubscribe_url"
                                ),
                                indicators=subscription_info.get(
                                    "indicators", []
                                )
                            )
                            result["subscription_detected"] = True
                            result["subscription_type"] = subscription_info.get(
                                "type", "Email Subscription"
                            )
                            result["unsubscribe_url"] = subscription_info.get(
                                "unsubscribe_url"
                            )
                    except Exception as sub_error:
                        result["subscription_error"] = str(sub_error)

                except Exception as email_error:
                    result = {
                        "message_id": message_id,
                        "sender": "Unknown",
                        "subject": "Could not analyze email",
                        "body": "",
                        "date": "",
                        "ml_prediction": "ERROR",
                        "ml_score": 0,
                        "confidence": 0,
                        "trusted_sender": False,
                        "rule_score": 0,
                        "indicators": [str(email_error)],
                        "final_prediction": "ERROR",
                        "gmail_action": "ANALYSIS ERROR",
                        "subscription_detected": False
                    }

                # Save immediately, including error results, to avoid
                # losing already completed work if a later page fails.
                save_email_history(result)
                results.append(result)
                processed_ids.add(str(message_id))

                if not scan_all and len(results) >= int(max_results):
                    return results

            if not scan_all:
                break

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return results

    except Exception as error:
        return {
            "error": (
                "Gmail analysis stopped. Results already saved remain in "
                "Email History. Details: " + str(error)
            )
        }
# ============================================================
# MOVE EMAIL TO GMAIL SPAM
# ============================================================

def move_email_to_spam(
    message_id
):

    if not message_id:

        return (
            False,
            "Message ID is missing."
        )

    try:

        service = get_gmail_service()

        if service is None:

            return (
                False,
                "Gmail service could not be created."
            )

        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={
                "addLabelIds": ["SPAM"]
            }
        ).execute()

        return (
            True,
            "Moved to Gmail Spam."
        )

    except Exception as error:

        return (
            False,
            str(error)
        )

# ============================================================
# SMART GMAIL CLEANUP
# ============================================================

IMPORTANT_EMAIL_KEYWORDS = [
    "security alert",
    "password",
    "verification code",
    "verify your account",
    "suspicious login",
    "new sign-in",
    "account access",
    "job alert",
    "job opportunity",
    "interview",
    "application update",
    "recruiter",
    "job offer",
    "interview invitation",
    "connection request",
    "message from",
    "invitation",
]


def get_cleanup_emails(max_messages=100, page_size=20):
    """Fetch a bounded batch of received Gmail messages for user-reviewed cleanup.

    Gmail's messages.get call is made once per message, so scanning every page
    of a large mailbox can exhaust the per-user API quota. This fetches up to
    max_messages matching emails, using smaller list pages and the shared
    retry helper for temporary quota/server errors.
    """
    try:
        from email_system.gmail_classifier import (
            get_header,
            extract_body,
        )

        service = get_gmail_service()
        if service is None:
            return [], "Gmail service could not be created."

        emails = []
        page_token = None
        seen_ids = set()
        quota_stopped = False
        quota_note = None
        max_messages = max(1, min(int(max_messages), 200))
        page_size = max(1, min(int(page_size), 25))

        while len(seen_ids) < max_messages:
            params = {
                "userId": "me",
                "q": "-in:spam -in:trash -in:sent -in:drafts",
                "maxResults": min(page_size, max_messages - len(seen_ids)),
            }
            if page_token:
                params["pageToken"] = page_token

            response = execute_gmail_request(
                service.users().messages().list(**params)
            )

            message_infos = response.get("messages", [])
            if not message_infos:
                break

            for message_info in message_infos:
                message_id = message_info.get("id")
                if not message_id or message_id in seen_ids:
                    continue
                seen_ids.add(message_id)

                try:
                    message = execute_gmail_request(
                        service.users().messages().get(
                            userId="me",
                            id=message_id,
                            format="full",
                        )
                    )

                    payload = message.get("payload", {})
                    headers = payload.get("headers", [])
                    sender = get_header(headers, "From")
                    subject = get_header(headers, "Subject")
                    date = get_header(headers, "Date")
                    body = extract_body(payload) or ""

                    ml_prediction, ml_score = classify_email(subject, body)
                    final_prediction = hybrid_decision(
                        ml_prediction, ml_score, sender, subject, body,
                    )
                    searchable = (str(subject) + " " + str(body)).casefold()
                    important_reasons = [
                        keyword for keyword in IMPORTANT_EMAIL_KEYWORDS
                        if keyword in searchable
                    ]
                    is_important = (
                        bool(important_reasons)
                        or str(final_prediction).upper() == "HAM"
                    )

                    emails.append({
                        "Select for deletion": False,
                        "Date": date,
                        "Sender": sender,
                        "Subject": subject or "(No subject)",
                        "Prediction": str(final_prediction).upper(),
                        "Importance": (
                            "Review / likely important"
                            if is_important else "Potentially unwanted"
                        ),
                        "Why flagged": ", ".join(important_reasons),
                        "message_id": message_id,
                    })

                except Exception as email_error:
                    error_text = str(email_error).lower()
                    if any(term in error_text for term in (
                        "ratelimitexceeded", "userratelimitexceeded",
                        "quota exceeded", "units per minute per user",
                    )):
                        quota_stopped = True
                        quota_note = (
                            "Gmail API quota was reached during this fetch. "
                            "The messages already inspected are available below; "
                            "wait about a minute before fetching again."
                        )
                        break
                    # Never auto-select messages that could not be inspected.
                    emails.append({
                        "Select for deletion": False,
                        "Date": "",
                        "Sender": "",
                        "Subject": "Could not inspect this email",
                        "Prediction": "ERROR",
                        "Importance": "Manual review required",
                        "Why flagged": str(email_error),
                        "message_id": message_id,
                    })

                if quota_stopped or len(seen_ids) >= max_messages:
                    break

            if quota_stopped:
                break
            page_token = response.get("nextPageToken")
            if not page_token or len(seen_ids) >= max_messages:
                break

        note = quota_note
        if note is None and len(emails) >= max_messages:
            note = (
                f"Loaded the first {max_messages} matching emails to protect "
                "your Gmail API quota. Fetch again later for a fresh batch."
            )
        return emails, note

    except Exception as error:
        return emails if "emails" in locals() else [], str(error)


def move_message_to_trash(message_id):
    """Move one Gmail message to Trash; do not change local history."""
    if not message_id:
        return False, "Missing Gmail message ID."

    try:
        service = get_gmail_service()

        if service is None:
            return False, "Gmail service could not be created."

        service.users().messages().trash(
            userId="me",
            id=message_id,
        ).execute()

        return True, "Moved to Gmail Trash."

    except Exception as error:
        return False, str(error)
# ============================================================
# UPDATE EMAIL PREDICTION AFTER HUMAN REVIEW
# ============================================================

def update_email_prediction(
    message_id,
    new_prediction
):

    if not message_id:
        return False

    new_prediction = str(new_prediction).upper()

    if new_prediction not in [
        "SPAM",
        "HAM"
    ]:
        return False

    history = load_history()
    updated = False

    for item in history:
        if item.get("message_id") == message_id:
            item["final_prediction"] = new_prediction
            item["gmail_action"] = (
                "USER MARKED AS SPAM"
                if new_prediction == "SPAM"
                else "USER MARKED AS SAFE"
            )
            item["reviewed_at"] = datetime.now().isoformat()
            item["reviewed_by"] = "USER"
            updated = True
            break

    if not updated:
        return False

    return save_json_file(
        HISTORY_FILE,
        history
    )

# ============================================================
# EMAIL SECURITY REPORT
# ============================================================

def build_email_security_report():

    history = load_history()
    subscriptions = load_subscriptions()

    total = len(history)
    spam = sum(1 for item in history if str(item.get("final_prediction", "")).upper() == "SPAM")
    ham = sum(1 for item in history if str(item.get("final_prediction", "")).upper() == "HAM")
    uncertain = sum(1 for item in history if str(item.get("final_prediction", "")).upper() == "UNCERTAIN")
    errors = sum(1 for item in history if str(item.get("final_prediction", "")).upper() == "ERROR")

    phishing_high = sum(1 for item in history if str(item.get("phishing_risk", "")).upper() == "HIGH")
    phishing_medium = sum(1 for item in history if str(item.get("phishing_risk", "")).upper() == "MEDIUM")
    phishing_low = sum(1 for item in history if str(item.get("phishing_risk", "")).upper() == "LOW")
    suspicious_urls = sum(len(item.get("suspicious_urls", []) or []) for item in history)

    reviewed = [item for item in history if item.get("reviewed_by")]
    corrections = sum(
        1 for item in reviewed
        if str(item.get("ml_prediction", "")).upper()
        != str(item.get("final_prediction", "")).upper()
    )
    feedback_spam = sum(1 for item in reviewed if str(item.get("final_prediction", "")).upper() == "SPAM")
    feedback_safe = sum(1 for item in reviewed if str(item.get("final_prediction", "")).upper() == "HAM")

    active_subscriptions = sum(
        1 for item in subscriptions
        if str(item.get("status", "active")).lower() == "active"
    )
    inactive_subscriptions = max(len(subscriptions) - active_subscriptions, 0)

    alerts_file = os.path.join(os.path.dirname(HISTORY_FILE), "security_alerts.json")
    alerts = load_json_file(alerts_file, [])
    if not isinstance(alerts, list):
        alerts = []
    unread_alerts = sum(1 for item in alerts if not item.get("read", False))

    spam_rate = (spam / total * 100) if total else 0
    review_rate = (len(reviewed) / total * 100) if total else 0

    if spam > ham:
        overall_status = "HIGH SECURITY ATTENTION"
    elif phishing_high > 0 or unread_alerts > 0:
        overall_status = "SECURITY ATTENTION REQUIRED"
    else:
        overall_status = "NORMAL"

    generated_at = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    return {
        "generated_at": generated_at,
        "overall_status": overall_status,
        "total": total,
        "spam": spam,
        "ham": ham,
        "uncertain": uncertain,
        "errors": errors,
        "spam_rate": spam_rate,
        "phishing_high": phishing_high,
        "phishing_medium": phishing_medium,
        "phishing_low": phishing_low,
        "suspicious_urls": suspicious_urls,
        "reviewed": len(reviewed),
        "corrections": corrections,
        "feedback_spam": feedback_spam,
        "feedback_safe": feedback_safe,
        "review_rate": review_rate,
        "subscriptions": len(subscriptions),
        "active_subscriptions": active_subscriptions,
        "inactive_subscriptions": inactive_subscriptions,
        "alerts": len(alerts),
        "unread_alerts": unread_alerts,
    }


def create_report_html(report):

    def esc(value):
        return html.escape(str(value))

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Smart Email Security Report</title>
<style>
body {{ font-family: Arial, sans-serif; background:#f8fafc; color:#1e293b; margin:40px; }}
.container {{ max-width:1000px; margin:auto; background:white; padding:36px; border-radius:16px; }}
h1 {{ margin-bottom:4px; }}
.subtitle {{ color:#64748b; margin-bottom:28px; }}
.status {{ padding:14px 18px; border-radius:10px; background:#eef2ff; font-weight:bold; margin-bottom:24px; }}
.grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:20px 0 30px; }}
.card {{ border:1px solid #e2e8f0; border-radius:12px; padding:16px; }}
.value {{ font-size:26px; font-weight:bold; margin-top:5px; }}
.label {{ color:#64748b; font-size:13px; }}
h2 {{ margin-top:30px; border-bottom:1px solid #e2e8f0; padding-bottom:8px; }}
table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
th,td {{ border:1px solid #e2e8f0; padding:10px; text-align:left; }}
th {{ background:#f1f5f9; }}
.footer {{ color:#64748b; font-size:12px; margin-top:35px; }}
</style>
</head>
<body>
<div class="container">
<h1>📧 Smart Email System</h1>
<div class="subtitle">Machine Learning Based Secondary Spam Mail Detection Using Data Balancing Techniques</div>
<div class="status">Overall Security Status: {esc(report['overall_status'])}<br>Generated: {esc(report['generated_at'])}</div>

<h2>Security Overview</h2>
<div class="grid">
<div class="card"><div class="label">Total Emails</div><div class="value">{report['total']}</div></div>
<div class="card"><div class="label">Spam Detected</div><div class="value">{report['spam']}</div></div>
<div class="card"><div class="label">Safe Emails</div><div class="value">{report['ham']}</div></div>
<div class="card"><div class="label">Needs Review</div><div class="value">{report['uncertain']}</div></div>
</div>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Spam Rate</td><td>{report['spam_rate']:.2f}%</td></tr>
<tr><td>Analysis Errors</td><td>{report['errors']}</td></tr>
<tr><td>High Phishing Risk</td><td>{report['phishing_high']}</td></tr>
<tr><td>Medium Phishing Risk</td><td>{report['phishing_medium']}</td></tr>
<tr><td>Low Phishing Risk</td><td>{report['phishing_low']}</td></tr>
<tr><td>Suspicious URLs</td><td>{report['suspicious_urls']}</td></tr>
</table>

<h2>Subscriptions</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total Subscriptions</td><td>{report['subscriptions']}</td></tr>
<tr><td>Active</td><td>{report['active_subscriptions']}</td></tr>
<tr><td>Inactive</td><td>{report['inactive_subscriptions']}</td></tr>
</table>

<h2>User Feedback & Learning</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Reviewed Emails</td><td>{report['reviewed']}</td></tr>
<tr><td>Review Rate</td><td>{report['review_rate']:.2f}%</td></tr>
<tr><td>Corrections Made</td><td>{report['corrections']}</td></tr>
<tr><td>User Marked SPAM</td><td>{report['feedback_spam']}</td></tr>
<tr><td>User Marked SAFE</td><td>{report['feedback_safe']}</td></tr>
</table>

<h2>Security Alerts</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total Alerts</td><td>{report['alerts']}</td></tr>
<tr><td>Unread Alerts</td><td>{report['unread_alerts']}</td></tr>
</table>

<h2>Recommended Actions</h2>
<ul>
<li>Review all emails marked as high phishing risk.</li>
<li>Review uncertain emails before taking action.</li>
<li>Use the subscription manager to remove unwanted mailing lists.</li>
<li>Continue providing user feedback to improve the labeled training set.</li>
</ul>

<div class="footer">Generated by Smart Email System.</div>
</div>
</body>
</html>"""

# ============================================================
# GOOGLE SIGN-IN + PER-USER DATA
# ============================================================

def user_data_paths(google_sub):
    """Return isolated data paths for one Google identity."""
    safe_id = hashlib.sha256(google_sub.encode("utf-8")).hexdigest()
    folder = os.path.join(USER_DATA_DIR, safe_id)
    os.makedirs(folder, exist_ok=True)
    return {
        "folder": folder,
        "history": os.path.join(folder, "email_history.json"),
        "subscriptions": os.path.join(folder, "subscriptions.json"),
        "alerts": os.path.join(folder, "security_alerts.json"),
    }


def initialize_user_data(google_sub):
    """Copy legacy files to the first Google user's folder once; never remove originals."""
    paths = user_data_paths(google_sub)
    owner = load_json_file(LEGACY_OWNER_FILE, {})
    if not owner.get("google_sub"):
        # Preserve the existing files and copy them to the first user's private folder.
        for source, destination in (
            (os.path.join(DATA_DIR, "email_history.json"), paths["history"]),
            (os.path.join(DATA_DIR, "subscriptions.json"), paths["subscriptions"]),
        ):
            if os.path.isfile(source) and not os.path.exists(destination):
                shutil.copy2(source, destination)
        save_json_file(LEGACY_OWNER_FILE, {"google_sub": google_sub})
    elif owner.get("google_sub") == google_sub:
        for source, destination in (
            (os.path.join(DATA_DIR, "email_history.json"), paths["history"]),
            (os.path.join(DATA_DIR, "subscriptions.json"), paths["subscriptions"]),
        ):
            if os.path.isfile(source) and not os.path.exists(destination):
                shutil.copy2(source, destination)
    # A different Google user receives their own empty data files, not another user's data.
    if not os.path.exists(paths["history"]):
        save_json_file(paths["history"], [])
    if not os.path.exists(paths["subscriptions"]):
        save_json_file(paths["subscriptions"], [])
    return paths


def google_client_configured():
    return os.path.isfile(GOOGLE_OAUTH_CLIENT_FILE)


def google_oauth_flow(state=None, code_verifier=None, autogenerate_code_verifier=False):
    """Create the OAuth flow, preserving the PKCE verifier across the redirect."""
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_secrets_file(
        GOOGLE_OAUTH_CLIENT_FILE,
        scopes=GOOGLE_SCOPES,
        state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=autogenerate_code_verifier,
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow


def clear_google_login_state():
    for key in (
        "authenticated_user", "google_user_sub", "google_user_email",
        "google_user_name", "google_oauth_state", "google_oauth_url",
        "gmail_results", "selected_subscriptions", "cleanup_auto_fetch_attempted",
    ):
        st.session_state.pop(key, None)


if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

# Handle the OAuth redirect from Google.
query_params = st.query_params
returned_code = query_params.get("code")
returned_state = query_params.get("state")
if returned_code and not st.session_state.get("authenticated_user"):
    saved_states = load_json_file(GOOGLE_OAUTH_STATES_FILE, {})
    state_record = saved_states.get(str(returned_state)) if returned_state else None
    # Support old timestamp-only entries, but they do not contain a PKCE verifier
    # and therefore cannot complete the current authorization attempt.
    if isinstance(state_record, dict):
        state_created = state_record.get("created_at")
        saved_code_verifier = state_record.get("code_verifier")
    else:
        state_created = state_record
        saved_code_verifier = None
    try:
        state_valid = bool(
            state_created is not None
            and saved_code_verifier
            and (time.time() - float(state_created) <= 600)
            and (time.time() - float(state_created) >= 0)
        )
    except (TypeError, ValueError):
        state_valid = False
    if not state_valid:
        st.error("Google sign-in request expired or could not be verified. Please click Continue with Google and try again.")
        st.query_params.clear()
    elif not google_client_configured():
        st.error("Google OAuth client file is missing. Add google_oauth_client.json to the project folder.")
    else:
        try:
            saved_states.pop(str(returned_state), None)
            save_json_file(GOOGLE_OAUTH_STATES_FILE, saved_states)
            flow = google_oauth_flow(
                state=str(returned_state),
                code_verifier=str(saved_code_verifier),
            )
            flow.fetch_token(code=str(returned_code))
            credentials = flow.credentials
            from google.oauth2 import id_token
            from google.auth.transport.requests import Request
            claims = id_token.verify_oauth2_token(
                credentials.id_token, Request(), flow.client_config["client_id"]
            )
            google_sub = str(claims.get("sub", ""))
            google_email = str(claims.get("email", ""))
            if not google_sub or not google_email or not claims.get("email_verified", False):
                raise ValueError("Google did not return a verified email identity.")
            os.makedirs(GOOGLE_TOKEN_DIR, exist_ok=True)
            token_file = os.path.join(
                GOOGLE_TOKEN_DIR,
                hashlib.sha256(google_sub.encode("utf-8")).hexdigest() + ".json",
            )
            with open(token_file, "w", encoding="utf-8") as token_out:
                token_out.write(credentials.to_json())
            paths = initialize_user_data(google_sub)
            # Redirect all dashboard reads/writes to this user's own files.
            HISTORY_FILE = paths["history"]
            SUBSCRIPTIONS_FILE = paths["subscriptions"]
            st.session_state.google_user_sub = google_sub
            st.session_state.google_user_email = google_email
            st.session_state.google_user_name = str(claims.get("name", google_email))
            st.session_state.authenticated_user = google_email
            st.session_state.pop("google_oauth_state", None)
            st.session_state.pop("google_oauth_url", None)
            st.query_params.clear()
            st.rerun()
        except Exception as error:
            st.error(f"Google sign-in could not be completed: {error}")
            st.query_params.clear()

# When returning to an existing Streamlit session, load that Google user's data paths.
if st.session_state.get("authenticated_user") and st.session_state.get("google_user_sub"):
    current_paths = initialize_user_data(st.session_state.google_user_sub)
    HISTORY_FILE = current_paths["history"]
    SUBSCRIPTIONS_FILE = current_paths["subscriptions"]

if not st.session_state.get("authenticated_user"):
    st.markdown(
        "<div style='text-align:center; padding-top:2rem;'>"
        "<h1>📧 Smart Email System</h1>"
        "<p>Sign in securely with Google, then authorize the Gmail account you want to manage.</p></div>",
        unsafe_allow_html=True,
    )
    _, auth_col, _ = st.columns([1, 1.2, 1])
    with auth_col:
        if not google_client_configured():
            st.error("Google OAuth setup is required before sign-in can work.")
            st.markdown(
                "1. In Google Cloud Console, create an OAuth client ID of type **Web application**.\n"
                "2. Add `http://localhost:8501` as an authorized redirect URI.\n"
                "3. Download the client JSON, rename it to `google_oauth_client.json`, and place it beside `dashboard.py`.\n"
                "4. Enable the **Gmail API** and configure the OAuth consent screen."
            )
            st.caption("For a deployed app, set GOOGLE_REDIRECT_URI to the deployed callback URL and register that exact URL in Google Cloud.")
        else:
            if "google_oauth_url" not in st.session_state:
                st.session_state.google_oauth_url = None
            if st.button("Continue with Google", type="primary", use_container_width=True):
                try:
                    # PKCE: generate a verifier for this login and persist it with
                    # the OAuth state so it survives Google's browser redirect and
                    # Streamlit reruns/session reconnection.
                    flow = google_oauth_flow(autogenerate_code_verifier=True)
                    authorization_url, state = flow.authorization_url(
                        access_type="offline",
                        include_granted_scopes="true",
                        prompt="consent select_account",
                    )
                    saved_states = load_json_file(GOOGLE_OAUTH_STATES_FILE, {})
                    now = time.time()
                    fresh_states = {}
                    for saved_state, record in saved_states.items():
                        try:
                            created_at = (
                                record.get("created_at")
                                if isinstance(record, dict)
                                else record
                            )
                            if created_at is not None and 0 <= now - float(created_at) <= 600:
                                fresh_states[saved_state] = record
                        except (TypeError, ValueError, AttributeError):
                            continue
                    saved_states = fresh_states
                    if not flow.code_verifier:
                        raise RuntimeError("OAuth PKCE verifier was not generated. Please update google-auth-oauthlib.")
                    saved_states[state] = {
                        "created_at": now,
                        "code_verifier": flow.code_verifier,
                    }
                    save_json_file(GOOGLE_OAUTH_STATES_FILE, saved_states)
                    st.session_state.google_oauth_state = state
                    st.session_state.google_oauth_url = authorization_url
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not start Google sign-in: {error}")
            if st.session_state.get("google_oauth_url"):
                st.markdown(
                    f'<a href="{html.escape(st.session_state.google_oauth_url, quote=True)}" target="_self" '
                    'style="display:block;text-align:center;padding:0.8rem;background:#4285F4;color:white;'
                    'border-radius:8px;text-decoration:none;font-weight:600;">Open Google sign-in</a>',
                    unsafe_allow_html=True,
                )
    st.stop()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "📧 Smart Email System"
)
st.sidebar.caption(f"Google account: {st.session_state.get('google_user_email', st.session_state.authenticated_user)}")
if st.sidebar.button("Sign out", use_container_width=True, key="logout_button"):
    clear_google_login_state()
    st.query_params.clear()
    st.rerun()

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="text-align:center;">
            <p style="margin-top:-10px;">
                🛡️ AI-Powered Email Security
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()
    page = st.radio(
        "Go to",
        [
            "🏠 Dashboard",
            "🛡️ Email Security",
            "📋 Email History",
            "🗑️ Gmail Cleanup",
            "📬 Subscriptions",
            "👤 User Feedback",
            "📄 Email Security Report",
            "⚙️ Settings"
        ],
        label_visibility="collapsed",
        key="main_navigation"
    )

    st.divider()

    st.markdown("### 🎨 Appearance")

    dark_mode = st.toggle(
        "🌙 Dark Mode",
        value=False,
        key="dark_mode"
    )
    st.divider()

# ============================================================
# COHESIVE DESIGN SYSTEM
# ============================================================

if dark_mode:
    theme_tokens = """
    --app-bg: #0B1220;
    --surface: #111B2D;
    --surface-muted: #0F192A;
    --text-primary: #F1F5F9;
    --text-secondary: #A7B4C8;
    --border: #2A3951;
    --border-strong: #3A4D68;
    --accent: #7297FF;
    --accent-hover: #8BAAFF;
    --accent-soft: #1D3155;
    --focus-ring: #93B4FF;
    --shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
    """
else:
    theme_tokens = """
    --app-bg: #F4F7FB;
    --surface: #FFFFFF;
    --surface-muted: #F8FAFD;
    --text-primary: #17243A;
    --text-secondary: #52627A;
    --border: #DCE4EF;
    --border-strong: #B8C6D9;
    --accent: #3157D5;
    --accent-hover: #2446B8;
    --accent-soft: #EDF2FF;
    --focus-ring: #3157D5;
    --shadow: 0 8px 24px rgba(21, 39, 71, 0.055);
    """

DESIGN_SYSTEM_CSS = """
<style>
.stApp {
    __THEME_TOKENS__
    color: var(--text-primary) !important;
    background: var(--app-bg) !important;
    font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 15px;
    line-height: 1.55;
}
[data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stMain"], .main, .block-container {
    color: var(--text-primary) !important;
    background: var(--app-bg) !important;
}
.block-container { width: 100%; max-width: 1500px; padding: clamp(1.1rem, 2.5vw, 2.5rem) clamp(.85rem, 3vw, 2.75rem) 3rem; }
[data-testid="stHeader"] { background: transparent !important; }

/* Type scale and page headings */
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    color: var(--text-primary) !important; letter-spacing: -.025em; line-height: 1.25;
}
h1 { font-size: clamp(1.8rem, 3vw, 2.35rem) !important; font-weight: 750 !important; }
h2 { font-size: clamp(1.35rem, 2.2vw, 1.7rem) !important; font-weight: 700 !important; }
h3 { font-size: 1.12rem !important; font-weight: 700 !important; }
p, li, [data-testid="stMarkdownContainer"] { color: var(--text-primary); }
[data-testid="stCaptionContainer"], small { color: var(--text-secondary) !important; }
.main-title { color: var(--text-primary) !important; font-size: clamp(1.9rem, 3.5vw, 2.55rem); font-weight: 780; letter-spacing: -.045em; line-height: 1.12; margin: 0 0 .45rem; }
.subtitle { color: var(--text-secondary) !important; font-size: 1rem; line-height: 1.65; margin: 0 0 1.65rem; max-width: 76ch; }
a { color: var(--accent) !important; text-underline-offset: 3px; }
a:hover { text-decoration-thickness: 2px; }
hr { border-color: var(--border) !important; }

/* Sidebar navigation */
section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div { background: var(--surface) !important; color: var(--text-primary) !important; }
section[data-testid="stSidebar"] { border-right: 1px solid var(--border); }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: var(--text-primary) !important; }
section[data-testid="stSidebar"] h1 { font-size: 1.08rem !important; letter-spacing: -.02em; }
section[data-testid="stSidebar"] [role="radiogroup"] { gap: .25rem; }
section[data-testid="stSidebar"] [role="radiogroup"] label { border: 1px solid transparent; border-radius: 10px; padding: .38rem .55rem; transition: background-color 140ms ease, border-color 140ms ease; }
section[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: var(--surface-muted) !important; border-color: var(--border) !important; }
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: var(--accent-soft) !important; border-color: var(--border-strong) !important; }

/* Metrics, cards and expandable details */
div[data-testid="stMetric"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 14px !important; padding: 1rem 1.1rem !important; box-shadow: var(--shadow); min-width: 0; transition: border-color 140ms ease, box-shadow 140ms ease; }
div[data-testid="stMetric"]:hover { border-color: var(--border-strong) !important; }
div[data-testid="stMetricLabel"], div[data-testid="stMetricDelta"] { color: var(--text-secondary) !important; }
div[data-testid="stMetricValue"] { color: var(--text-primary) !important; font-weight: 750 !important; letter-spacing: -.035em; }
div[data-testid="stExpander"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; overflow: clip; }
div[data-testid="stExpander"] summary, div[data-testid="stExpander"] summary p { color: var(--text-primary) !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--border) !important; border-radius: 14px !important; }

/* Buttons and clear interactive states */
.stButton > button, .stDownloadButton > button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stPopover"] > div > button {
    min-height: 2.55rem; border-radius: 9px !important; font-weight: 650 !important;
    transition: background-color 140ms ease, border-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
}
.stButton > button { background: var(--accent) !important; color: #FFFFFF !important; border: 1px solid var(--accent) !important; }
.stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover { background: var(--accent-hover) !important; border-color: var(--accent-hover) !important; box-shadow: 0 4px 12px rgba(49, 87, 213, .18); }
.stButton > button:active, .stDownloadButton > button:active { transform: translateY(1px); }
.stDownloadButton > button, [data-testid="stPopover"] > div > button { background: var(--surface) !important; color: var(--text-primary) !important; border: 1px solid var(--border-strong) !important; }
.stDownloadButton > button:hover, [data-testid="stPopover"] > div > button:hover { border-color: var(--accent) !important; }
button:disabled, button[disabled] { opacity: .58 !important; cursor: not-allowed !important; box-shadow: none !important; }

/* Form fields and dropdown surfaces */
div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div { background: var(--surface) !important; border-color: var(--border-strong) !important; border-radius: 9px !important; }
input, textarea, [data-baseweb="select"] input { color: var(--text-primary) !important; caret-color: var(--accent) !important; }
input::placeholder, textarea::placeholder { color: var(--text-secondary) !important; opacity: .9; }
[data-baseweb="select"] span { color: var(--text-primary) !important; }
[data-testid="stCheckbox"] label, [data-testid="stRadio"] label,
[data-testid="stToggle"] label, [data-testid="stSlider"] label { color: var(--text-primary) !important; }
[data-baseweb="popover"], [data-baseweb="popover"] ul,
[data-baseweb="popover"] li, [data-baseweb="menu"] { background: var(--surface) !important; color: var(--text-primary) !important; border-color: var(--border) !important; }

/* Tabs, alerts, tables and native Streamlit data components */
button[data-baseweb="tab"] { color: var(--text-secondary) !important; font-weight: 650 !important; }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--accent) !important; }
div[data-testid="stAlert"] { border: 1px solid var(--border) !important; border-radius: 11px !important; }
div[data-testid="stDataFrame"], div[data-testid="stTable"] { border: 1px solid var(--border) !important; border-radius: 11px !important; overflow: hidden; }
[data-testid="stStatusWidget"] { border-color: var(--border) !important; }

/* Keyboard focus and reduced-motion preferences */
:where(button, a, input, textarea, [role="radio"], [role="checkbox"], [role="tab"], [tabindex]):focus-visible { outline: 3px solid var(--focus-ring) !important; outline-offset: 2px !important; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition-duration: .01ms !important; animation-duration: .01ms !important; scroll-behavior: auto !important; } }
@media (max-width: 768px) {
    .block-container { padding: 1.1rem .85rem 2rem; }
    .main-title { font-size: clamp(1.65rem, 7vw, 2.1rem); }
    .subtitle { font-size: .94rem; margin-bottom: 1.2rem; }
    div[data-testid="stMetric"] { padding: .8rem !important; border-radius: 11px !important; }
    div[data-testid="stMetricValue"] { font-size: 1.35rem !important; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: .65rem !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width: min(100%, 230px) !important; flex: 1 1 230px !important; }
    section[data-testid="stSidebar"] { border-right: 0; }
}
@media (max-width: 420px) { .block-container { padding-left: .65rem; padding-right: .65rem; } .stButton > button, .stDownloadButton > button { width: 100%; } }
</style>
"""

st.markdown(
    DESIGN_SYSTEM_CSS.replace("__THEME_TOKENS__", theme_tokens),
    unsafe_allow_html=True
)

# Apply the professional website-wide UI refresh
ui_css_path = Path(__file__).with_name("ui_styles.css")

if ui_css_path.exists():
    with open(ui_css_path, "r", encoding="utf-8") as css_file:
        ui_css = css_file.read()

    st.markdown(
        f"<style>{ui_css}</style>",
        unsafe_allow_html=True
    )
# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown(
        '<div class="main-title">Smart Email System</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Machine Learning Based Secondary Spam Mail Detection '
        '</div>',
        unsafe_allow_html=True
    )

    history = load_history()

    # ============================================================
    # CALCULATE DASHBOARD STATISTICS
    # ============================================================

    total = len(history)

    spam = sum(
        1
        for item in history
        if str(
            item.get(
                "final_prediction",
                ""
            )
        ).upper() == "SPAM"
    )

    ham = sum(
        1
        for item in history
        if str(
            item.get(
                "final_prediction",
                ""
            )
        ).upper() == "HAM"
    )

    uncertain = sum(
        1
        for item in history
        if str(
            item.get(
                "final_prediction",
                ""
            )
        ).upper() == "UNCERTAIN"
    )

    errors = sum(
        1
        for item in history
        if str(
            item.get(
                "final_prediction",
                ""
            )
        ).upper() == "ERROR"
    )

    spam_rate = (
        spam / total * 100
        if total
        else 0
    )

    # ============================================================
    # DASHBOARD SUMMARY
    # ============================================================

    st.subheader(
        "📊 Security Overview"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "📨 Total Emails",
            total
        )

    with c2:
        st.metric(
            "🚨 Spam Detected",
            spam
        )

    with c3:
        st.metric(
            "✅ Safe Emails",
            ham
        )

    with c4:
        st.metric(
            "⚠️ Needs Review",
            uncertain
        )

    st.divider()

    # ============================================================
    # SECURITY ANALYTICS
    # ============================================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "🚨 Spam Detection Rate"
        )

        st.progress(
            min(
                spam_rate / 100,
                1.0
            )
        )

        st.metric(
            "Current Spam Rate",
            f"{spam_rate:.2f}%"
        )

        if spam_rate >= 50:

            st.warning(
                "⚠️ High spam activity detected."
            )

        elif spam_rate >= 20:

            st.info(
                "ℹ️ Moderate spam activity detected."
            )

        else:

            st.success(
                "✅ Spam activity is currently low."
            )

    with col2:

        st.subheader(
            "📊 Classification Distribution"
        )

        chart_data = {
            "SPAM": spam,
            "SAFE": ham,
            "NEEDS REVIEW": uncertain,
            "ERROR": errors
        }

        st.bar_chart(
            chart_data,
            height=280
        )

    st.divider()

    # ============================================================
    # SYSTEM STATUS
    # ============================================================

    st.subheader(
        "🟢 System Status"
    )

    s1, s2, s3 = st.columns(3)

    with s1:

        if model_error:

            st.error(
                "❌ ML Model Error"
            )

            st.caption(
                model_error
            )

        else:

            st.success(
                "🟢 ML Model Online"
            )

            st.caption(
                "LinearSVC + TF-IDF"
            )

    with s2:

        if os.path.exists(
            HISTORY_FILE
        ):

            st.success(
                "🟢 Email History Connected"
            )

            st.caption(
                "History database available"
            )

        else:

            st.info(
                "🟡 Email History Ready"
            )

            st.caption(
                "No history file found yet"
            )

    with s3:

        if os.path.exists(
            SUBSCRIPTIONS_FILE
        ):

            st.success(
                "🟢 Subscription Data Connected"
            )

            st.caption(
                "Subscription manager available"
            )

        else:

            st.info(
                "🟡 Subscription Data Ready"
            )

            st.caption(
                "No subscription data found yet"
            )

    st.divider()

    # ============================================================
    # RECENT EMAIL ACTIVITY
    # ============================================================

    st.subheader(
        "📩 Recent Email Activity"
    )

    recent = list(
        reversed(
            history[-10:]
        )
    )

    if recent:

        for index, item in enumerate(recent):

            prediction = str(
                item.get(
                    "final_prediction",
                    ""
                )
            ).upper()

            if prediction == "SPAM":

                icon = "🚨"
                status_text = "SPAM"

            elif prediction == "HAM":

                icon = "✅"
                status_text = "SAFE"

            elif prediction == "UNCERTAIN":

                icon = "⚠️"
                status_text = "NEEDS REVIEW"

            else:

                icon = "❌"
                status_text = "ERROR"

            subject = item.get(
                "subject",
                "No Subject"
            )

            sender = item.get(
                "sender",
                "Unknown Sender"
            )

            date = item.get(
                "date",
                "Unknown Date"
            )

            with st.container(border=True):

                col1, col2, col3 = st.columns([1, 4, 1])

                with col1:
                    st.markdown(
                        f"## {icon}"
                    )

                with col2:

                    st.markdown(
                        f"**{status_text}**"
                    )

                    st.write(
                        f"📧 **{subject}**"
                    )

                    st.caption(
                        f"From: {sender}"
                    )

                    st.caption(
                        f"📅 {date}"
                    )

                with col3:

                    try:
                        confidence = float(
                            item.get(
                                "confidence",
                                0
                            )
                        )
                    except Exception:
                        confidence = 0

                    st.metric(
                        "Confidence",
                        f"{confidence:.1f}%"
                    )
    else:

        st.info(
            "📭 No email analysis history available yet."
        )
    
# ============================================================
# EMAIL SECURITY
# ============================================================

elif page == "🛡️ Email Security":

    st.markdown(
        '<div class="main-title">Email Security</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">AI-powered email classification, human review, and security analytics</div>',
        unsafe_allow_html=True
    )

    # Use conditional navigation instead of st.tabs(). Streamlit tabs execute
    # every tab's content on each rerun, which can make this page slow when
    # email history is large. A radio selector renders only the chosen section.
    security_section = st.radio(
        "Security section",
        [
            "🔍 Analyze Email",
            "⚠️ Needs Review",
            "📊 Security Statistics"
        ],
        horizontal=True,
        key="security_section_navigation",
        label_visibility="collapsed",
    )

    # ========================================================
    # TAB 1 - ANALYZE EMAIL
    # ========================================================

    if security_section == "🔍 Analyze Email":

        st.subheader("Analyze an Email")

        st.write(
            "Enter an email manually to test the hybrid ML + rule-based detection system."
        )

        sender = st.text_input(
            "Sender Email",
            placeholder="example@gmail.com",
            key="security_sender"
        )

        subject = st.text_input(
            "Email Subject",
            key="security_subject"
        )

        body = st.text_area(
            "Email Body",
            height=250,
            key="security_body"
        )

        if st.button(
            "🔍 Analyze Email",
            width='stretch',
            key="security_analyze_button"
        ):

            if not subject and not body:

                st.warning(
                    "Please enter an email subject or body."
                )

            else:

                ml_prediction, ml_score = classify_email(
                    subject,
                    body
                )

                trusted_sender, rule_score, indicators = rule_analysis(
                    sender,
                    subject,
                    body
                )

                final_prediction = hybrid_decision(
                    ml_prediction,
                    ml_score,
                    sender,
                    subject,
                    body
                )

                confidence = calculate_confidence(
                    ml_score
                )

                smart_analysis = generate_smart_analysis(
                    ml_prediction,
                    ml_score,
                    confidence,
                    trusted_sender,
                    rule_score,
                    indicators,
                    final_prediction
                )

                phishing_analysis = analyze_phishing_risk(
                    sender,
                    subject,
                    body
                )

                                # ====================================================
                # PROFESSIONAL ANALYSIS RESULT
                # ====================================================

                st.subheader("🧠 Smart Analysis")

                # ----------------------------------------------------
                # FINAL RESULT
                # ----------------------------------------------------

                if final_prediction == "SPAM":

                    st.error(
                        "🚨 SPAM DETECTED — This email appears unsafe."
                    )

                elif final_prediction == "HAM":

                    st.success(
                        "✅ SAFE EMAIL — This email appears legitimate."
                    )

                else:

                    st.warning(
                        "⚠️ UNCERTAIN EMAIL — Manual review recommended."
                    )

                # ----------------------------------------------------
                # SMART ANALYSIS SUMMARY
                # ----------------------------------------------------

                st.markdown("### 🔎 Security Assessment")

                st.write(
                    f"**Risk Level:** "
                    f"{smart_analysis['risk_level']}"
                )

                st.write(
                    "**Recommendation:** "
                    + smart_analysis["recommendation"]
                )

                # ----------------------------------------------------
                # REASONS
                # ----------------------------------------------------

                st.markdown("### 💡 Why was this result given?")

                if smart_analysis["reasons"]:

                    for reason in smart_analysis["reasons"]:

                        st.write(
                            "• " + reason
                        )

                else:

                    st.info(
                        "No additional reasons were identified."
                    )

                st.divider()

                # ----------------------------------------------------
                # ANALYSIS METRICS
                # ----------------------------------------------------

                st.markdown("### 📊 Detection Metrics")

                c1, c2, c3 = st.columns(3)

                with c1:

                    st.metric(
                        "🤖 ML Prediction",
                        ml_prediction
                    )

                with c2:

                    st.metric(
                        "📈 ML Score",
                        f"{ml_score:.4f}"
                    )

                with c3:

                    st.metric(
                        "🎯 Confidence",
                        f"{confidence:.2f}%"
                    )

                # ----------------------------------------------------
                # RULE-BASED ANALYSIS
                # ----------------------------------------------------

                st.markdown("### 🛡️ Rule-Based Analysis")

                r1, r2 = st.columns(2)

                with r1:

                    st.metric(
                        "Rule Score",
                        rule_score
                    )

                with r2:

                    st.metric(
                        "Trusted Sender",
                        "YES" if trusted_sender else "NO"
                    )

                # ----------------------------------------------------
                # SPAM INDICATORS
                # ----------------------------------------------------

                st.markdown("### ⚠️ Spam Indicators")

                if indicators:

                    for indicator in indicators:

                        st.warning(
                            "• " + indicator
                        )

                else:

                    st.success(
                        "✅ No spam indicators detected."
                    )

                # ----------------------------------------------------
                # PHISHING / URL SECURITY
                # ----------------------------------------------------

                st.markdown("### 🎣 Phishing & URL Security")

                p1, p2 = st.columns(2)

                with p1:

                    st.metric(
                        "Phishing Risk",
                        phishing_analysis["risk_level"]
                    )

                with p2:

                    st.metric(
                        "URL Risk Score",
                        phishing_analysis["score"]
                    )

                if phishing_analysis["urls"]:

                    st.write(
                        f"**Links detected:** {len(phishing_analysis['urls'])}"
                    )

                    if phishing_analysis["suspicious_urls"]:
                        st.warning(
                            "⚠️ Potentially risky link(s) detected. "
                            "Do not open them unless you trust the destination."
                        )
                        st.write("**Suspicious URL(s):**")
                        for suspicious_url in phishing_analysis["suspicious_urls"]:
                            st.code(suspicious_url, language=None)
                    else:
                        st.success("No suspicious URL-specific indicators were detected.")

                else:
                    st.info("No links were found in this email.")

                if phishing_analysis["reasons"]:
                    st.write("**Risk indicators and explanation:**")
                    for phishing_reason in phishing_analysis["reasons"]:
                        st.write("• " + phishing_reason)

                if phishing_analysis["risk_level"] == "HIGH":
                    st.error("High phishing risk: do not click links or share credentials without independently verifying the sender.")
                elif phishing_analysis["risk_level"] == "MEDIUM":
                    st.warning("Medium phishing risk: verify the sender and destination before responding.")
                else:
                    st.caption("Low heuristic risk does not guarantee that an email is safe.")

                history_item = {
                    "message_id": "manual_" + datetime.now().strftime("%Y%m%d%H%M%S%f"),
                    "sender": sender if sender else "Manual Test",
                    "subject": subject,
                    "body": body,
                    "date": datetime.now().isoformat(),
                    "ml_prediction": ml_prediction,
                    "ml_score": ml_score,
                    "confidence": confidence,
                    "trusted_sender": trusted_sender,
                    "rule_score": rule_score,
                    "indicators": indicators,
                    "phishing_risk": phishing_analysis["risk_level"],
                    "phishing_score": phishing_analysis["score"],
                    "suspicious_urls": phishing_analysis["suspicious_urls"],
                    "phishing_reasons": phishing_analysis["reasons"],
                    "final_prediction": final_prediction,
                    "gmail_action": "MANUAL TEST"
                }

                if save_email_history(history_item):
                    st.success("Email analysis saved to history.")
                else:
                    st.info(
                        "Analysis completed. This email already exists in history or could not be saved."
                    )

        # ========================================================
        # AUTOMATIC EMAIL ANALYSIS
        # ========================================================

        st.divider()

        st.subheader("🤖 Automatic Email Analysis")

        st.write(
            "Automatically check your Gmail inbox and analyze new emails "
            "using the ML + rule-based spam detection system."
        )

        auto_scan = st.toggle(
            "Enable Automatic Email Analysis",
            value=False,
            key="automatic_email_analysis"
        )
        automatic_spam_action = st.toggle(
            "🚨 Automatically move detected spam to Gmail Spam",
            value=False,
            key="automatic_spam_action"
        )

        if automatic_spam_action:
            st.warning(
                "⚠️ Emails classified as SPAM will automatically be "
                "moved to your Gmail Spam folder."
            )
        else:
            st.info(
                "Automatic spam action is disabled. "
                "Detected spam will only be reported."
            )

        if auto_scan:

            st.success(
                "🟢 Automatic Email Analysis is enabled."
            )

            scan_limit = st.number_input(
                "Emails to check per scan",
                min_value=1,
                max_value=50,
                value=10,
                step=1,
                key="automatic_scan_limit"
            )

            st.caption(
                "The system will automatically check Gmail when the "
                "dashboard is opened or refreshed."
            )

           
            # ----------------------------------------------------
            # AUTOMATIC GMAIL MONITOR
            # ----------------------------------------------------

            @st.fragment(run_every="60s")
            def automatic_gmail_monitor():
                """Poll Gmail periodically while automatic analysis is enabled.

                The fragment wakes every 60 seconds, but Gmail is scanned no
                more than once every 5 minutes. analyze_gmail_emails() already
                persists each processed message, so this function must not save
                the returned records a second time.
                """
                if "last_auto_scan" not in st.session_state:
                    st.session_state.last_auto_scan = None

                now = datetime.now()
                last_scan = st.session_state.last_auto_scan

                should_scan = (
                    last_scan is None
                    or (now - last_scan).total_seconds() >= 300
                )

                if not should_scan:
                    st.caption("Automatic monitoring is active. Next Gmail check is scheduled within 5 minutes.")
                    return

                # Capture the IDs before scanning so we can accurately report
                # which records were new. The analyzer itself saves each result.
                processed_before_scan = get_processed_message_ids()

                with st.spinner(
                    "🤖 Automatically checking Gmail for new emails..."
                ):
                    result = analyze_gmail_emails(scan_limit)

                # Record the attempt time even when Gmail returns an error, so
                # a temporary failure does not trigger API calls every 60 sec.
                st.session_state.last_auto_scan = now

                if isinstance(result, dict) and "error" in result:
                    st.error(
                        "Automatic Gmail scan failed: "
                        + str(result["error"])
                    )
                    return

                new_results = []
                if isinstance(result, list):
                    new_results = [
                        item for item in result
                        if item.get("message_id")
                        and str(item.get("message_id")) not in processed_before_scan
                    ]

                # Moving messages is opt-in and only applies to messages
                # classified as SPAM by the combined classifier.
                moved_to_spam = 0
                move_failures = 0
                if automatic_spam_action:
                    for item in new_results:
                        if str(item.get("final_prediction", "")).strip().upper() != "SPAM":
                            continue

                        message_id = item.get("message_id")
                        moved, _move_message = move_email_to_spam(message_id)
                        if moved:
                            moved_to_spam += 1
                            # Keep the history action consistent with the
                            # Gmail action that was actually completed.
                            history = load_history()
                            for history_item in history:
                                if str(history_item.get("message_id", "")) == str(message_id):
                                    history_item["gmail_action"] = "MOVED TO SPAM"
                                    break
                            save_json_file(HISTORY_FILE, history)
                        else:
                            move_failures += 1

                if new_results:
                    st.success(
                        f"🆕 {len(new_results)} new email(s) analyzed and saved to Email History."
                    )
                    if automatic_spam_action:
                        st.info(
                            f"Automatic spam action: {moved_to_spam} moved to Gmail Spam; "
                            f"{move_failures} could not be moved."
                        )

                    # Refresh the page-level statistics and history after the
                    # fragment has persisted new results.
                    st.rerun()
                else:
                    st.info("📭 No new emails found in the inbox.")
                    if automatic_spam_action and move_failures:
                        st.warning(
                            f"{move_failures} spam email(s) could not be moved to Gmail Spam."
                        )

            # Start monitoring. Without this call, the fragment is only
            # defined and Streamlit never schedules its periodic execution.
            automatic_gmail_monitor()
    # ========================================================
    # TAB 2 - NEEDS REVIEW
    # ========================================================

    elif security_section == "⚠️ Needs Review":

        st.subheader("⚠️ Emails Requiring Review")
   

        history = load_history()

        # Get all uncertain emails
        uncertain_emails = []

        for item in history:

            prediction = str(
                item.get(
                    "final_prediction",
                    ""
                )
            ).strip().upper()

            if prediction == "UNCERTAIN":
                uncertain_emails.append(item)

        # Debug / count
        st.info(
            f"🔎 {len(uncertain_emails)} email(s) currently require review."
        )

        if not uncertain_emails:

            st.success(
                "🎉 No uncertain emails pending review."
            )

        else:

            review_page_size = 10
            review_page_count = max(1, (len(uncertain_emails) + review_page_size - 1) // review_page_size)
            saved_review_page = int(st.session_state.get("security_review_page", 1) or 1)
            saved_review_page = min(max(saved_review_page, 1), review_page_count)
            st.session_state["security_review_page"] = saved_review_page
            review_page = st.number_input(
                "Needs Review page",
                min_value=1,
                max_value=review_page_count,
                step=1,
                key="security_review_page",
            )
            review_start = (int(review_page) - 1) * review_page_size
            visible_uncertain_emails = uncertain_emails[review_start:review_start + review_page_size]
            st.caption(f"Showing {review_start + 1}–{min(review_start + review_page_size, len(uncertain_emails))} of {len(uncertain_emails)} emails requiring review.")

            for index, item in enumerate(
                visible_uncertain_emails,
                start=review_start,
            ):

                message_id = item.get(
                    "message_id",
                    ""
                )

                subject_display = item.get(
                    "subject",
                    "No Subject"
                )

                sender_display = item.get(
                    "sender",
                    "Unknown"
                )

                with st.container(
                    border=True
                ):

                    # --------------------------------------------
                    # EMAIL HEADER
                    # --------------------------------------------

                    st.markdown(
                        f"### ⚠️ {subject_display}"
                    )

                    st.write(
                        "**Sender:**",
                        sender_display
                    )

                    st.write(
                        "**Date:**",
                        item.get(
                            "date",
                            "Unknown"
                        )
                    )

                    # --------------------------------------------
                    # CONFIDENCE
                    # --------------------------------------------

                    try:

                        confidence = float(
                            item.get(
                                "confidence",
                                0
                            )
                        )

                    except Exception:

                        confidence = 0.0

                    st.write(
                        "**Confidence:**",
                        f"{confidence:.2f}%"
                    )

                    # --------------------------------------------
                    # ML PREDICTION
                    # --------------------------------------------

                    st.write(
                        "**ML Prediction:**",
                        item.get(
                            "ml_prediction",
                            "Unknown"
                        )
                    )

                    # --------------------------------------------
                    # DETECTION DETAILS
                    # --------------------------------------------

                    st.write(
                        "**Rule Score:**",
                        item.get(
                            "rule_score",
                            0
                        )
                    )

                    indicators = item.get(
                        "indicators",
                        []
                    )

                    if indicators:

                        st.write(
                            "**Spam Indicators:**"
                        )

                        for indicator in indicators:

                            st.write(
                                f"• {indicator}"
                            )

                    else:

                        st.write(
                            "**Spam Indicators:** None"
                        )

                    # --------------------------------------------
                    # EMAIL CONTENT
                    # --------------------------------------------

                    with st.expander(
                        "📩 View Email Content"
                    ):

                        st.write(
                            "**Subject:**",
                            item.get(
                                "subject",
                                "No Subject"
                            )
                        )

                        st.write(
                            "**Sender:**",
                            item.get(
                                "sender",
                                "Unknown"
                            )
                        )

                        st.write(
                            "**Date:**",
                            item.get(
                                "date",
                                "Unknown"
                            )
                        )

                        st.divider()

                        st.write(
                            "**Email Body:**"
                        )

                        email_body = item.get(
                            "body",
                            "No email body available."
                        )

                        if email_body:
                            import re
                            from html import unescape

                            body_text = str(email_body).strip()

                            # Display HTML emails with their formatting
                            if re.search(r"<\s*(html|body|div|p|table|br|h[1-6]|ul|li)\b",
                                        body_text, re.IGNORECASE):

                                # Streamlit renders and sanitizes the HTML.
                                # Use the actual email body; clean_html was undefined.
                                st.html(body_text)

                            else:
                                st.markdown(body_text)

                        else:
                            st.info("Email body is not available for this record.")

                    # --------------------------------------------
                    # REVIEW ACTIONS
                    # --------------------------------------------

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "🚨 Mark as SPAM",
                            key=f"review_spam_{message_id}_{index}",
                            width='stretch'
                        ):

                            updated = update_email_prediction(
                                message_id,
                                "SPAM"
                            )

                            if updated:

                                # Move real Gmail email to Spam
                                if (
                                    message_id
                                    and not str(
                                        message_id
                                    ).startswith("manual_")
                                ):

                                    move_email_to_spam(
                                        message_id
                                    )

                                st.success(
                                    "Email marked as SPAM."
                                )

                                st.rerun()

                            else:

                                st.error(
                                    "Could not update this email."
                                )

                    with col2:

                        if st.button(
                            "✅ Mark as SAFE",
                            key=f"review_safe_{message_id}_{index}",
                            width='stretch'
                        ):

                            updated = update_email_prediction(
                                message_id,
                                "HAM"
                            )

                            if updated:

                                st.success(
                                    "Email marked as SAFE."
                                )

                                st.rerun()

                            else:

                                st.error(
                                    "Could not update this email."
                                )        
    # ========================================================
    # TAB 3 - SECURITY STATISTICS
    # ========================================================

    elif security_section == "📊 Security Statistics":

        st.subheader("📊 Security Statistics")

        history = load_history()

        stats = calculate_security_statistics(history)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "📧 Total Analyzed",
                stats["total"]
            )

        with col2:
            st.metric(
                "🟢 Safe",
                stats["ham"]
            )

        with col3:
            st.metric(
                "🔴 Spam",
                stats["spam"]
            )

        with col4:
            st.metric(
                "🟡 Needs Review",
                stats["uncertain"]
            )

        st.divider()

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "🛡️ Spam Detection Rate",
                f"{stats['spam_rate']:.2f}%"
            )

        with col2:

            st.metric(
                "⚠️ Review Required",
                stats["uncertain"]
            )

        st.divider()

        st.subheader("Classification Distribution")

        total = stats["total"]

        if total > 0:

            st.write(
                f"🚨 **Spam:** {stats['spam']} "
                f"({stats['spam'] / total * 100:.2f}%)"
            )

            st.write(
                f"🟢 **Safe:** {stats['ham']} "
                f"({stats['ham'] / total * 100:.2f}%)"
            )

            st.write(
                f"🟡 **Uncertain:** {stats['uncertain']} "
                f"({stats['uncertain'] / total * 100:.2f}%)"
            )

        else:

            st.info(
                "No email analysis data is available yet."
            )

# ============================================================
# EMAIL HISTORY
# ============================================================

elif page == "🗑️ Gmail Cleanup":

    st.markdown(
        '<div class="main-title">Gmail Cleanup</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="subtitle">Review emails by sender and move selected messages to Gmail Trash</div>',
        unsafe_allow_html=True
    )

    # ========================================================
    # SMART GMAIL CLEANUP - ALL SENDERS
    # ========================================================

    st.divider()
    st.subheader("🧹 Smart Gmail Cleanup")
    st.write(
        "Automatically scan Gmail and optionally move detected spam to Gmail Trash. "
        "Manual sender-by-sender selection remains available below."
    )
    st.caption(
        "Each scan reviews up to 100 received messages and excludes Gmail Spam, "
        "Trash, Sent, and Drafts. Automatic cleanup is opt-in and only moves messages "
        "classified SPAM that are not marked important. Trash is reversible; no "
        "permanent deletion is performed, and data/email_history.json is untouched."
    )
    st.checkbox(
        "Enable automatic cleanup: move detected, non-important SPAM to Gmail Trash after each scan",
        key="auto_trash_detected_spam",
        value=st.session_state.get("auto_trash_detected_spam", False),
        help="Only messages classified SPAM and not flagged as likely important are moved. This is not permanent deletion."
    )

    if "cleanup_emails" not in st.session_state:
        st.session_state.cleanup_emails = []
    if "cleanup_sender_groups" not in st.session_state:
        st.session_state.cleanup_sender_groups = None
    if "cleanup_selected_ids" not in st.session_state:
        st.session_state.cleanup_selected_ids = set()
    if "cleanup_pending_delete" not in st.session_state:
        st.session_state.cleanup_pending_delete = []
    if "cleanup_auto_fetch_attempted" not in st.session_state:
        st.session_state.cleanup_auto_fetch_attempted = False

    def update_cleanup_email_selection(message_id):
        widget_key = f"cleanup_email_{message_id}"
        if st.session_state.get(widget_key, False):
            st.session_state.cleanup_selected_ids.add(message_id)
        else:
            st.session_state.cleanup_selected_ids.discard(message_id)

    def update_cleanup_sender_selection(sender_ids, sender_widget_key):
        select_sender = st.session_state.get(sender_widget_key, False)
        for message_id in sender_ids:
            email_widget_key = f"cleanup_email_{message_id}"
            # Callback runs before the page widgets are created on rerun.
            st.session_state[email_widget_key] = select_sender
            if select_sender:
                st.session_state.cleanup_selected_ids.add(message_id)
            else:
                st.session_state.cleanup_selected_ids.discard(message_id)

    def load_cleanup_emails(show_success=True):
        with st.spinner("Fetching Gmail messages and preparing the sender list..."):
            emails, error = get_cleanup_emails()

        # Optional automated cleanup runs once per fetch, not on every rerun.
        # Only trash messages classified SPAM and not flagged as likely important.
        auto_trashed = 0
        auto_failed = []
        if emails and st.session_state.get("auto_trash_detected_spam", False):
            candidates = [
                item for item in emails
                if str(item.get("Prediction", "")).upper() == "SPAM"
                and str(item.get("Importance", "")).casefold() == "potentially unwanted"
                and item.get("message_id")
            ]
            for item in candidates:
                ok, detail = move_message_to_trash(str(item["message_id"]))
                if ok:
                    auto_trashed += 1
                    item["Cleanup status"] = "Automatically moved to Gmail Trash"
                else:
                    auto_failed.append((item.get("Subject", "(No subject)"), detail))
                    item["Cleanup status"] = "Auto-cleanup failed; review manually"

        if emails:
            st.session_state.cleanup_emails = emails
            # Rebuild sender groups only after a fresh Gmail fetch.
            st.session_state.cleanup_sender_groups = None
            st.session_state.cleanup_selected_ids = set()
            st.session_state.cleanup_pending_delete = []
            # Clear old widget state so a fresh scan starts with no selections.
            for key in list(st.session_state.keys()):
                if key.startswith("cleanup_email_") or key.startswith("cleanup_sender_all_"):
                    del st.session_state[key]
            if show_success:
                st.success(f"Loaded {len(emails)} message(s) for review.")
            if auto_trashed:
                st.info(f"Automatic cleanup moved {auto_trashed} detected spam message(s) to Gmail Trash.")
            if auto_failed:
                st.warning(f"Automatic cleanup could not move {len(auto_failed)} message(s). They remain in Gmail.")
            if error:
                st.warning(f"Fetch note: {error}")
            st.rerun()
        elif error:
            st.error(f"Could not fetch Gmail messages: {error}")

    # Automatically fetch the first batch the first time Gmail Cleanup is opened
    # in a Streamlit session. If opt-in automatic cleanup is enabled, eligible SPAM
    # candidates are moved to Gmail Trash during that fetch.
    if not st.session_state.cleanup_auto_fetch_attempted and not st.session_state.cleanup_emails:
        st.session_state.cleanup_auto_fetch_attempted = True
        load_cleanup_emails(show_success=False)

    if st.button("🔄 Refresh emails from all senders", key="fetch_all_cleanup_emails"):
        st.session_state.cleanup_auto_fetch_attempted = True
        load_cleanup_emails(show_success=True)

    cleanup_emails = st.session_state.cleanup_emails

    if cleanup_emails:
        import pandas as pd
        from email.utils import parseaddr

        # Group by sender once per fetched Gmail result. Rebuilding this for every
        # Streamlit rerun is expensive when the cleanup list contains many emails.
        if st.session_state.cleanup_sender_groups is None:
            sender_groups = {}
            for email_item in cleanup_emails:
                sender_text = str(email_item.get("Sender", "")).strip()
                parsed_name, parsed_address = parseaddr(sender_text)
                group_key = (parsed_address or sender_text or "Unknown sender").casefold()
                display_sender = sender_text or "Unknown sender — inspection failed"
                if group_key not in sender_groups:
                    sender_groups[group_key] = {"display": display_sender, "emails": []}
                sender_groups[group_key]["emails"].append(email_item)

            st.session_state.cleanup_sender_groups = sorted(
                sender_groups.items(),
                key=lambda item: item[1]["display"].casefold(),
            )

        sorted_sender_groups = st.session_state.cleanup_sender_groups
        st.write(f"**Senders found:** {len(sorted_sender_groups)}")
        st.write(f"**Selected emails:** {len(st.session_state.cleanup_selected_ids)}")
        st.caption("Expand a sender below. Select individual messages, or use the sender-level checkbox to select all selectable messages from that sender.")
        sender_page_size = 10
        sender_page_count = max(1, (len(sorted_sender_groups) + sender_page_size - 1) // sender_page_size)
        saved_sender_page = int(st.session_state.get("cleanup_sender_page", 1) or 1)
        saved_sender_page = min(max(saved_sender_page, 1), sender_page_count)
        st.session_state["cleanup_sender_page"] = saved_sender_page
        sender_page = st.number_input(
            "Sender list page",
            min_value=1,
            max_value=sender_page_count,
            step=1,
            key="cleanup_sender_page",
        )
        sender_start = (int(sender_page) - 1) * sender_page_size
        visible_sender_groups = sorted_sender_groups[sender_start:sender_start + sender_page_size]
        st.caption(f"Showing sender groups {sender_start + 1}–{min(sender_start + sender_page_size, len(sorted_sender_groups))} of {len(sorted_sender_groups)}. Selections are retained when changing pages.")

        for group_index, (group_key, group) in enumerate(visible_sender_groups, start=sender_start):
            group_emails = group["emails"]
            selectable_ids = [
                str(item.get("message_id", ""))
                for item in group_emails
                if item.get("message_id") and str(item.get("Prediction", "")).upper() != "ERROR"
            ]
            selected_in_group = sum(
                1 for message_id in selectable_ids
                if message_id in st.session_state.cleanup_selected_ids
            )
            with st.expander(f"✉️ {group['display']}  ·  {len(group_emails)} email(s)  ·  {selected_in_group} selected", expanded=False):
                sender_widget_key = "cleanup_sender_all_" + str(group_index)
                all_selected = bool(selectable_ids) and all(
                    message_id in st.session_state.cleanup_selected_ids
                    for message_id in selectable_ids
                )
                st.checkbox(
                    "Select all selectable emails from this sender",
                    value=all_selected,
                    key=sender_widget_key,
                    on_change=update_cleanup_sender_selection,
                    args=(selectable_ids, sender_widget_key),
                    disabled=not selectable_ids,
                )

                for email_index, email_item in enumerate(group_emails):
                    message_id = str(email_item.get("message_id", ""))
                    inspection_failed = str(email_item.get("Prediction", "")).upper() == "ERROR" or not message_id
                    subject = str(email_item.get("Subject", "(No subject)"))
                    date = str(email_item.get("Date", ""))
                    prediction = str(email_item.get("Prediction", "UNKNOWN"))
                    importance = str(email_item.get("Importance", "Review manually"))
                    why_flagged = str(email_item.get("Why flagged", ""))

                    email_col, detail_col = st.columns([1, 8])
                    with email_col:
                        st.checkbox(
                            "Select",
                            value=(message_id in st.session_state.cleanup_selected_ids),
                            key=f"cleanup_email_{message_id or 'unknown_' + str(group_index) + '_' + str(email_index)}",
                            on_change=update_cleanup_email_selection,
                            args=(message_id,),
                            disabled=inspection_failed,
                            label_visibility="visible",
                        )
                    with detail_col:
                        st.markdown(f"**{subject}**")
                        st.caption(f"Date: {date or 'Unknown'} · Prediction: {prediction} · Review: {importance}")
                        if why_flagged:
                            st.caption(f"Notes: {why_flagged}")
                        cleanup_status = str(email_item.get("Cleanup status", ""))
                        if cleanup_status:
                            st.caption(f"Cleanup status: {cleanup_status}")
                        if inspection_failed:
                            st.warning("This message could not be inspected, so it cannot be selected for bulk cleanup.")
                    st.divider()

        selected_ids = [
            str(email_item.get("message_id", ""))
            for email_item in cleanup_emails
            if str(email_item.get("message_id", "")) in st.session_state.cleanup_selected_ids
            and str(email_item.get("Prediction", "")).upper() != "ERROR"
        ]
        st.write(f"### Selected for Trash: {len(selected_ids)} email(s)")

        if st.button(
            "Continue to deletion confirmation",
            key="prepare_cleanup_delete",
            disabled=not selected_ids,
        ):
            st.session_state.cleanup_pending_delete = list(dict.fromkeys(selected_ids))
            st.rerun()

    pending_ids = st.session_state.cleanup_pending_delete
    if pending_ids:
        st.warning(
            f"You selected {len(pending_ids)} email(s) to move to Gmail Trash. "
            "This action changes Gmail only; data/email_history.json will not be edited."
        )
        confirm_delete = st.checkbox(
            "I reviewed these messages and confirm moving them to Gmail Trash.",
            key="confirm_cleanup_bulk_delete",
        )
        if st.button(
            "🗑️ Confirm and Move Selected Emails to Trash",
            type="primary",
            key="confirm_cleanup_bulk_delete_button",
            disabled=not confirm_delete,
        ):
            success_count = 0
            failed = []
            with st.spinner("Moving selected messages to Gmail Trash..."):
                for message_id in pending_ids:
                    success, message = move_message_to_trash(message_id)
                    if success:
                        success_count += 1
                    else:
                        failed.append((message_id, message))

            st.session_state.cleanup_pending_delete = []
            st.session_state.cleanup_selected_ids = set()
            st.session_state.cleanup_emails = []
            st.session_state.cleanup_sender_groups = None
            for key in list(st.session_state.keys()):
                if key.startswith("cleanup_email_") or key.startswith("cleanup_sender_all_"):
                    del st.session_state[key]
            st.success(f"Moved {success_count} email(s) to Gmail Trash.")
            if failed:
                st.error(f"{len(failed)} email(s) could not be moved.")
                for message_id, error_message in failed:
                    st.write(f"`{message_id}` — {error_message}")
            st.info("Email History was preserved; this cleanup feature does not modify data/email_history.json.")
            st.rerun()


elif page == "📋 Email History":

    st.markdown(
        '<div class="main-title">Email History</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Complete history of analyzed emails and security decisions'
        '</div>',
        unsafe_allow_html=True
    )

    history = load_history()
    if not history:

        st.info(
            "📭 No email history available yet."
        )

    else:

        # ====================================================
        # HISTORY SUMMARY
        # ====================================================

        total_count = len(history)

        spam_count = sum(
            1
            for item in history
            if str(
                item.get(
                    "final_prediction",
                    ""
                )
            ).upper() == "SPAM"
        )

        ham_count = sum(
            1
            for item in history
            if str(
                item.get(
                    "final_prediction",
                    ""
                )
            ).upper() == "HAM"
        )

        uncertain_count = sum(
            1
            for item in history
            if str(
                item.get(
                    "final_prediction",
                    ""
                )
            ).upper() == "UNCERTAIN"
        )

        error_count = sum(
            1
            for item in history
            if str(
                item.get(
                    "final_prediction",
                    ""
                )
            ).upper() == "ERROR"
        )

        h1, h2, h3, h4, h5 = st.columns(5)

        h1.metric(
            "📧 Total",
            total_count
        )

        h2.metric(
            "🚨 Spam",
            spam_count
        )

        h3.metric(
            "✅ Safe",
            ham_count
        )

        h4.metric(
            "⚠️ Review",
            uncertain_count
        )

        h5.metric(
            "❌ Errors",
            error_count
        )

        st.divider()

        # ====================================================
        # SEARCH AND FILTER
        # ====================================================

        col1, col2 = st.columns([2, 1])

        with col1:

            search = st.text_input(
                "🔎 Search emails",
                placeholder=(
                    "Search sender, subject, or email content..."
                ),
                key="email_history_search"
            )

        with col2:

            filter_option = st.selectbox(
                "🎯 Filter by status",
                [
                    "ALL",
                    "SPAM",
                    "HAM",
                    "UNCERTAIN",
                    "ERROR"
                ],
                key="email_history_filter"
            )

        # ====================================================
        # FILTER EMAILS
        # ====================================================

        filtered = []
        search_value = str(search or "").strip().casefold()

        for item in history:

            prediction = str(
                item.get(
                    "final_prediction",
                    ""
                )
            ).strip().upper()

            sender = str(
                item.get(
                    "sender",
                    ""
                )
            )

            subject = str(
                item.get(
                    "subject",
                    ""
                )
            )

            body = str(
                item.get(
                    "body",
                    ""
                )
            )

            # Build one complete searchable text so the search box
            # can find emails by sender, subject, body, message ID,
            # prediction, spam indicators, and phishing information.
            message_id = str(
                item.get(
                    "message_id",
                    ""
                )
            )

            ml_prediction = str(
                item.get(
                    "ml_prediction",
                    ""
                )
            )

            phishing_risk = str(
                item.get(
                    "phishing_risk",
                    ""
                )
            )

            indicators = " ".join(
                str(value)
                for value in item.get(
                    "indicators",
                    []
                )
            )

            suspicious_urls = " ".join(
                str(value)
                for value in item.get(
                    "suspicious_urls",
                    []
                )
            )

            if search_value:
                searchable_text = " ".join([
                    sender,
                    subject,
                    body,
                    message_id,
                    prediction,
                    ml_prediction,
                    phishing_risk,
                    indicators,
                    suspicious_urls
                ]).casefold()
                matches_search = search_value in searchable_text
            else:
                # The default view needs no full-body string construction.
                matches_search = True

            matches_filter = (
                filter_option == "ALL"
                or prediction == filter_option
            )

            if matches_search and matches_filter:

                filtered.append(item)
        col3, col4 = st.columns(2)

        with col3:
            sort_option = st.selectbox(
                "↕️ Sort emails",
                [
                    "Newest First",
                    "Oldest First",
                    "Highest Confidence",
                    "Lowest Confidence"
                ],
                key="email_history_sort"
            )

        with col4:
            st.caption(
                "For smoother scrolling, email bodies load only when you select them below."
            )
        def get_confidence(item):
            try:
                return float(item.get("confidence", 0) or 0)
            except Exception:
                return 0.0  
                  
        # ====================================================
        # SORT RESULTS
        # ====================================================

        if sort_option == "Newest First":
            filtered = sorted(
                filtered,
                key=lambda x: str(x.get("date", "")),
                reverse=True
            )

        elif sort_option == "Oldest First":
            filtered = sorted(
                filtered,
                key=lambda x: str(x.get("date", ""))
            )

        elif sort_option == "Highest Confidence":
            filtered = sorted(
                filtered,
                key=get_confidence,
                reverse=True
            )

        elif sort_option == "Lowest Confidence":
            filtered = sorted(
                filtered,
                key=get_confidence
            )       

        # ====================================================
        # RESULT COUNT
        # ====================================================

        st.write(
            f"📋 Showing **{len(filtered)}** "
            f"of **{len(history)}** analyzed emails."
        )

        # ====================================================
        # PAGINATE HISTORY RESULTS TO AVOID RENDERING HUNDREDS OF CARDS
        # ====================================================

        history_page_size = 10
        history_page_count = max(1, (len(filtered) + history_page_size - 1) // history_page_size)
        saved_history_page = int(st.session_state.get("history_page_number", 1) or 1)
        saved_history_page = min(max(saved_history_page, 1), history_page_count)
        st.session_state["history_page_number"] = saved_history_page
        history_page = st.number_input(
            "History results page",
            min_value=1,
            max_value=history_page_count,
            step=1,
            key="history_page_number",
        )
        history_start = (int(history_page) - 1) * history_page_size
        visible_history = filtered[history_start:history_start + history_page_size]
        st.caption(f"Displaying {history_start + 1 if filtered else 0}–{min(history_start + history_page_size, len(filtered))} of {len(filtered)} matching emails.")

        # ====================================================
        # EMAIL RECORDS
        # ====================================================

        if not filtered:

            st.warning(
                "🔍 No emails match your search/filter."
            )

        else:

            for index, item in enumerate(
                visible_history,
                start=history_start,
            ):

                prediction = str(
                    item.get(
                        "final_prediction",
                        ""
                    )
                ).strip().upper()

                # --------------------------------------------
                # STATUS ICON
                # --------------------------------------------

                if prediction == "SPAM":

                    icon = "🚨"

                elif prediction == "HAM":

                    icon = "✅"

                elif prediction == "UNCERTAIN":

                    icon = "⚠️"

                else:

                    icon = "❌"

                subject = item.get(
                    "subject",
                    "No Subject"
                )

                sender = item.get(
                    "sender",
                    "Unknown Sender"
                )

                # --------------------------------------------
                # EMAIL CARD
                # --------------------------------------------

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"### {icon} {prediction}"
                    )

                    st.write(
                        "**Subject:**",
                        subject
                    )

                    st.write(
                        "**Sender:**",
                        sender
                    )

                    st.write(
                        "**Date:**",
                        item.get(
                            "date",
                            "Unknown"
                        )
                    )

                    # ----------------------------------------
                    # ANALYSIS SUMMARY
                    # ----------------------------------------

                    a1, a2, a3 = st.columns(3)

                    with a1:

                        st.metric(
                            "ML Prediction",
                            item.get(
                                "ml_prediction",
                                "N/A"
                            )
                        )

                    with a2:

                        try:

                            confidence = float(
                                item.get(
                                    "confidence",
                                    0
                                )
                            )

                        except Exception:

                            confidence = 0.0

                        st.metric(
                            "Confidence",
                            f"{confidence:.2f}%"
                        )

                    with a3:

                        st.metric(
                            "Rule Score",
                            item.get(
                                "rule_score",
                                0
                            )
                        )

                    # ----------------------------------------
                    # EMAIL CONTENT
                    # ----------------------------------------

                    # Load large email bodies only on explicit request.
                    # Streamlit evaluates expander contents even when collapsed;
                    # a checkbox avoids rendering every stored body while scrolling.
                    history_record_id = str(
                        item.get("message_id")
                        or item.get("id")
                        or f"record_{index}"
                    )
                    show_this_body = st.checkbox(
                        "📩 Show email body",
                        value=False,
                        key=f"history_show_body_{history_record_id}"
                    )

                    if show_this_body:
                        st.write("**Email Body:**")
                        email_body = item.get("body", "")

                        if email_body:
                            import re
                            body_text = str(email_body).strip()
                            if re.search(
                                r"<\s*(html|body|div|p|table|br|h[1-6]|ul|li)\b",
                                body_text,
                                re.IGNORECASE,
                            ):
                                # Sanitized renderer for untrusted email HTML.
                                st.html(body_text)
                            else:
                                st.text(body_text)
                        else:
                            st.info("Email body is not available for this record.")

                    # ----------------------------------------
                    # DETECTION DETAILS
                    # ----------------------------------------

                    with st.expander(
                        "🧠 View Detection Details"
                    ):

                        d1, d2 = st.columns(2)

                        with d1:

                            st.write(
                                "**ML Prediction:**",
                                item.get(
                                    "ml_prediction",
                                    "N/A"
                                )
                            )

                            st.write(
                                "**ML Score:**",
                                item.get(
                                    "ml_score",
                                    0
                                )
                            )

                            st.write(
                                "**Confidence:**",
                                f"{confidence:.2f}%"
                            )

                        with d2:

                            st.write(
                                "**Final Prediction:**",
                                prediction
                            )

                            st.write(
                                "**Rule Score:**",
                                item.get(
                                    "rule_score",
                                    0
                                )
                            )

                            trusted = item.get(
                                "trusted_sender",
                                False
                            )

                            st.write(
                                "**Trusted Sender:**",
                                "YES"
                                if trusted
                                else "NO"
                            )

                        indicators = item.get(
                            "indicators",
                            []
                        )

                        st.divider()

                        st.write(
                            "**Phishing Risk:**",
                            item.get("phishing_risk", "LOW")
                        )

                        st.write(
                            "**Phishing URL Score:**",
                            item.get("phishing_score", 0)
                        )

                        suspicious_urls = item.get(
                            "suspicious_urls",
                            []
                        )

                        if suspicious_urls:
                            st.write("**Suspicious URLs:**")
                            for suspicious_url in suspicious_urls:
                                st.write("• " + str(suspicious_url))

                        phishing_reasons = item.get("phishing_reasons", [])
                        if phishing_reasons:
                            st.write("**Phishing risk indicators:**")
                            for phishing_reason in phishing_reasons:
                                st.write("• " + str(phishing_reason))

                        st.write(
                            "**Spam Indicators:**"
                        )

                        if indicators:

                            for indicator in indicators:

                                st.write(
                                    f"• {indicator}"
                                )

                        else:

                            st.write(
                                "None detected."
                            )

                    # ----------------------------------------
                    # REVIEW INFORMATION
                    # ----------------------------------------

                    reviewed_by = item.get(
                        "reviewed_by",
                        ""
                    )

                    reviewed_at = item.get(
                        "reviewed_at",
                        ""
                    )

                    gmail_action = item.get(
                        "gmail_action",
                        "N/A"
                    )

                    if reviewed_by or reviewed_at:

                        with st.expander(
                            "👤 Review Information"
                        ):

                            st.write(
                                "**Reviewed By:**",
                                reviewed_by
                            )

                            st.write(
                                "**Reviewed At:**",
                                reviewed_at
                            )

                            st.write(
                                "**Decision:**",
                                prediction
                            )

                    # ----------------------------------------
                    # GMAIL ACTION
                    # ----------------------------------------

                    st.write(
                        "**Gmail Action:**",
                        gmail_action
                    )

                    # ----------------------------------------
                    # MESSAGE ID
                    # ----------------------------------------

                    message_id = item.get(
                        "message_id",
                        ""
                    )

                    if message_id:

                        st.caption(
                            f"🆔 Message ID: {message_id}"
                        )

        # ====================================================
        # EXPORT FILTERED HISTORY
        # ====================================================

        st.divider()

        st.subheader(
            "📥 Export Analysis History"
        )

        csv_data = []

        for item in filtered:

            csv_data.append({

                "Message ID":
                    item.get(
                        "message_id",
                        ""
                    ),

                "Sender":
                    item.get(
                        "sender",
                        ""
                    ),

                "Subject":
                    item.get(
                        "subject",
                        ""
                    ),

                "body": item.get(
                    "body",
                    ""
                ),    

                "Date":
                    item.get(
                        "date",
                        ""
                    ),

                "ML Prediction":
                    item.get(
                        "ml_prediction",
                        ""
                    ),

                "ML Score":
                    item.get(
                        "ml_score",
                        0
                    ),

                "Confidence":
                    item.get(
                        "confidence",
                        0
                    ),

                "Trusted Sender":
                    item.get(
                        "trusted_sender",
                        False
                    ),

                "Rule Score":
                    item.get(
                        "rule_score",
                        0
                    ),

                "Spam Indicators":
                    ", ".join(
                        map(
                            str,
                            item.get(
                                "indicators",
                                []
                            )
                        )
                    ),

                "Final Prediction":
                    item.get(
                        "final_prediction",
                        ""
                    ),

                "Gmail Action":
                    item.get(
                        "gmail_action",
                        ""
                    ),

                "Reviewed By":
                    item.get(
                        "reviewed_by",
                        ""
                    ),

                "Reviewed At":
                    item.get(
                        "reviewed_at",
                        ""
                    )
            })

        if csv_data:

            import pandas as pd

            dataframe = pd.DataFrame(
                csv_data
            )

            st.download_button(
                "⬇️ Export Filtered History CSV",
                dataframe.to_csv(
                    index=False
                ),
                file_name="email_history.csv",
                mime="text/csv",
                key="export_email_history_csv"
            )
    # ============================================================
    # RESCAN EMAIL HISTORY FOR SUBSCRIPTIONS
    # ============================================================

    def rescan_subscriptions_from_history():

        history = load_history()

        detected_count = 0

        try:

            from email_system.subscription_manager import (
                add_subscription
            )

        except ImportError:

            return 0

        for item in history:

            sender = item.get(
                "sender",
                ""
            )

            subject = item.get(
                "subject",
                ""
            )

            body = item.get(
                "body",
                ""
            )

            subscription_info = detect_subscription(
                sender,
                subject,
                body
            )

            if subscription_info:

                add_subscription(
                    sender=sender,
                    subject=subject,
                    subscription_type=subscription_info["type"],
                    unsubscribe_url=subscription_info["unsubscribe_url"],
                    indicators=subscription_info["indicators"]
                )

                detected_count += 1

        return detected_count
# ============================================================
# UNSUBSCRIPTION MANAGER
# ============================================================

elif page == "📬 Subscriptions":

    st.title("📬 Subscription Management")
    st.caption(
        "Manage newsletters, promotional emails, and mailing-list subscriptions."
    )

    # ========================================================
    # LOAD SUBSCRIPTIONS
    # ========================================================

    subscriptions = load_subscriptions()

    # ========================================================
    # SCAN EXISTING EMAIL HISTORY FOR SUBSCRIPTIONS
    # ========================================================

    if st.button(
        "🔍 Scan Existing Emails for Subscriptions",
        key="scan_existing_subscriptions"
    ):

        detected_count = rescan_subscriptions_from_history()

        # Reload the existing subscription list after scanning
        subscriptions = load_subscriptions()

        if detected_count > 0:

            st.success(
                f"Detected {detected_count} subscription email(s)."
            )

            st.rerun()

        else:

            st.info(
                "No subscription emails were detected in the existing email history."
            )


    # ============================================================
    # SUBSCRIPTION ACTIONS
    # ============================================================

    def deactivate_subscription(sender_email):

        subscriptions = load_subscriptions()

        found = False

        for subscription in subscriptions:

            if (
                str(
                    subscription.get(
                        "sender_email",
                        ""
                    )
                ).lower()
                == str(sender_email).lower()
            ):

                subscription["status"] = "INACTIVE"

                subscription["deactivated_at"] = (
                    datetime.now().isoformat()
                )

                found = True

        if found:

            return save_json_file(
                SUBSCRIPTIONS_FILE,
                subscriptions
            )

        return False


    def activate_subscription(sender_email):

        subscriptions = load_subscriptions()

        found = False

        for subscription in subscriptions:

            if (
                str(
                    subscription.get(
                        "sender_email",
                        ""
                    )
                ).lower()
                == str(sender_email).lower()
            ):

                subscription["status"] = "ACTIVE"

                subscription["activated_at"] = (
                    datetime.now().isoformat()
                )

                found = True

        if found:

            return save_json_file(
                SUBSCRIPTIONS_FILE,
                subscriptions
            )

        return False


    def delete_subscription(sender_email):

        subscriptions = load_subscriptions()

        updated_subscriptions = []

        deleted = False

        for subscription in subscriptions:

            if (
                str(
                    subscription.get(
                        "sender_email",
                        ""
                    )
                ).lower()
                == str(sender_email).lower()
            ):

                deleted = True

            else:

                updated_subscriptions.append(
                    subscription
                )

        if deleted:

            return save_json_file(
                SUBSCRIPTIONS_FILE,
                updated_subscriptions
            )

        return False
    # ========================================================
    # SUMMARY
    # ========================================================

    total_subscriptions = len(subscriptions)

    active_subscriptions = sum(
        1
        for subscription in subscriptions
        if subscription.get("status", "ACTIVE") == "ACTIVE"
    )

    inactive_subscriptions = sum(
        1
        for subscription in subscriptions
        if subscription.get("status", "ACTIVE") == "INACTIVE"
    )


    # ========================================================
    # NO SUBSCRIPTIONS
    # ========================================================

    if not subscriptions:

        st.info(
            "No subscriptions have been detected yet."
        )

    else:

        # ====================================================
        # SEARCH + FILTER
        # ====================================================

        col1, col2 = st.columns([2, 1])

        with col1:

            search_subscription = st.text_input(
                "🔎 Search subscriptions",
                placeholder="Search by sender or email..."
            )

        with col2:

            subscription_filter = st.selectbox(
                "Status",
                [
                    "All",
                    "Active",
                    "Inactive"
                ]
            )

        # ====================================================
        # FILTER SUBSCRIPTIONS
        # ====================================================

        filtered_subscriptions = []

        for subscription in subscriptions:

            sender = str(
                subscription.get(
                    "sender",
                    ""
                )
            )

            sender_email = str(
                subscription.get(
                    "sender_email",
                    ""
                )
            )

            status = str(
                subscription.get(
                    "status",
                    "ACTIVE"
                )
            ).upper()

            # Search filter
            if search_subscription:

                search_text = (
                    sender
                    + " "
                    + sender_email
                ).lower()

                if search_subscription.lower() not in search_text:
                    continue

            # Status filter
            if (
                subscription_filter == "Active"
                and status != "ACTIVE"
            ):
                continue

            if (
                subscription_filter == "Inactive"
                and status != "INACTIVE"
            ):
                continue

            filtered_subscriptions.append(
                subscription
            )

        # ====================================================
        # RESULTS
        # ====================================================

        st.write(
            f"Showing **{len(filtered_subscriptions)}** "
            f"subscription(s)"
        )

        st.divider()


        # ====================================================
        # SUBSCRIPTION SELECTION
        # ====================================================

        # Make sure selection state exists
        if "selected_subscriptions" not in st.session_state:
            st.session_state.selected_subscriptions = set()

        if "subscriptions_select_all" not in st.session_state:
            st.session_state.subscriptions_select_all = False


        # ----------------------------------------------------
        # SELECT ALL CALLBACK
        # ----------------------------------------------------

        def select_all_subscriptions():

            if st.session_state.subscriptions_select_all:

                st.session_state.selected_subscriptions = {
                    str(
                        subscription.get(
                            "sender_email",
                            ""
                        )
                    ).strip()

                    for subscription
                    in filtered_subscriptions

                    if str(
                        subscription.get(
                            "sender_email",
                            ""
                        )
                    ).strip()
                }

            else:

                st.session_state.selected_subscriptions = set()


        # ----------------------------------------------------
        # INDIVIDUAL SELECTION CALLBACK
        # ----------------------------------------------------

        def update_subscription_selection(
            sender_email
        ):

            checkbox_key = (
                f"subscription_select_{sender_email}"
            )

            if st.session_state.get(
                checkbox_key,
                False
            ):

                st.session_state.selected_subscriptions.add(
                    sender_email
                )

            else:

                st.session_state.selected_subscriptions.discard(
                    sender_email
                )


        # ----------------------------------------------------
        # SELECT ALL CHECKBOX
        # ----------------------------------------------------

        st.checkbox(
            "☑️ Select All Subscriptions",
            key="subscriptions_select_all",
            on_change=select_all_subscriptions
        )


        # ----------------------------------------------------
        # SELECTED COUNT
        # ----------------------------------------------------

        selected_count = len(
            st.session_state.selected_subscriptions
        )

        if selected_count > 0:

            st.info(
                f"**{selected_count} subscription(s) selected**"
            )


        # ====================================================
        # BULK ACTIONS
        # ====================================================

        if selected_count > 0:

            st.subheader(
                "Selected Subscription Actions"
            )

            bulk_col1, bulk_col2, bulk_col3 = st.columns(3)


            # ------------------------------------------------
            # BULK DEACTIVATE
            # ------------------------------------------------

            with bulk_col1:

                if st.button(
                    "⏸️ Deactivate Selected",
                    width='stretch',
                    key="bulk_deactivate_subscriptions"
                ):

                    success_count = 0

                    for sender_email in list(
                        st.session_state.selected_subscriptions
                    ):

                        if deactivate_subscription(
                            sender_email
                        ):

                            success_count += 1

                    st.session_state.selected_subscriptions = set()

                    st.session_state.subscriptions_select_all = False

                    st.success(
                        f"{success_count} subscription(s) deactivated."
                    )

                    st.rerun()


            # ------------------------------------------------
            # BULK ACTIVATE
            # ------------------------------------------------

            with bulk_col2:

                if st.button(
                    "▶️ Activate Selected",
                    width='stretch',
                    key="bulk_activate_subscriptions"
                ):

                    success_count = 0

                    for sender_email in list(
                        st.session_state.selected_subscriptions
                    ):

                        if activate_subscription(
                            sender_email
                        ):

                            success_count += 1

                    st.session_state.selected_subscriptions = set()

                    st.session_state.subscriptions_select_all = False

                    st.success(
                        f"{success_count} subscription(s) activated."
                    )

                    st.rerun()


            # ------------------------------------------------
            # BULK DELETE
            # ------------------------------------------------

            with bulk_col3:

                if st.button(
                    "🗑️ Delete Selected",
                    width='stretch',
                    key="bulk_delete_subscriptions"
                ):

                    success_count = 0

                    for sender_email in list(
                        st.session_state.selected_subscriptions
                    ):

                        if delete_subscription(
                            sender_email
                        ):

                            success_count += 1

                    st.session_state.selected_subscriptions = set()

                    st.session_state.subscriptions_select_all = False

                    st.success(
                        f"{success_count} subscription(s) deleted."
                    )

                    st.rerun()


        st.divider()


        # ====================================================
        # DISPLAY SUBSCRIPTION CARDS
        # ====================================================

        for index, subscription in enumerate(
            filtered_subscriptions
        ):

            sender = subscription.get(
                "sender",
                "Unknown Sender"
            )

            sender_email = str(
                subscription.get(
                    "sender_email",
                    "Unknown Email"
                )
            ).strip()

            subscription_type = subscription.get(
                "type",
                "Subscription"
            )

            status = subscription.get(
                "status",
                "ACTIVE"
            )

            unsubscribe_url = subscription.get(
                "unsubscribe_url"
            )

            indicators = subscription.get(
                "indicators",
                []
            )

            last_seen = subscription.get(
                "last_seen",
                ""
            )


            # ------------------------------------------------
            # INDIVIDUAL SELECTION
            # ------------------------------------------------

            checkbox_key = (
                f"subscription_select_{sender_email}"
            )

            st.checkbox(
                "☑️ Select this subscription",
                key=checkbox_key,
                on_change=update_subscription_selection,
                args=(sender_email,)
            )


            # =================================================
            # CARD
            # =================================================

            with st.container(
                border=True
            ):

                col1, col2 = st.columns(
                    [4, 1]
                )


                # ------------------------------------------------
                # SENDER
                # ------------------------------------------------

                with col1:

                    st.subheader(
                        f"📧 {sender}"
                    )

                    st.caption(
                        sender_email
                    )


                # ------------------------------------------------
                # STATUS
                # ------------------------------------------------

                with col2:

                    if status == "ACTIVE":

                        st.success(
                            "🟢 ACTIVE"
                        )

                    else:

                        st.error(
                            "🔴 INACTIVE"
                        )


                st.write(
                    f"**Type:** {subscription_type}"
                )


                # ------------------------------------------------
                # INDICATORS
                # ------------------------------------------------

                if indicators:

                    st.write(
                        "**Detected indicators:** "
                        + ", ".join(
                            str(indicator)
                            for indicator in indicators
                        )
                    )


                # ------------------------------------------------
                # LAST SEEN
                # ------------------------------------------------

                if last_seen:

                    st.caption(
                        f"Last detected: {last_seen}"
                    )


                st.divider()


                # =================================================
                # EXISTING ACTION BUTTONS
                # =================================================

                col1, col2, col3 = st.columns(
                    [1, 1, 2]
                )


                # ------------------------------------------------
                # UNSUBSCRIBE
                # ------------------------------------------------

                with col1:

                    if unsubscribe_url:

                        st.link_button(
                            "🔕 Unsubscribe",
                            unsubscribe_url,
                            width='stretch'
                        )

                    else:

                        st.button(
                            "🔕 No Link",
                            disabled=True,
                            width='stretch',
                            key=f"no_unsub_{index}"
                        )


                # ------------------------------------------------
                # ACTIVATE / DEACTIVATE
                # ------------------------------------------------

                with col2:

                    if status == "ACTIVE":

                        if st.button(
                            "⏸️ Deactivate",
                            key=f"deactivate_{index}_{sender_email}",
                            width='stretch'
                        ):

                            sender_email_value = (
                                subscription.get(
                                    "sender_email",
                                    ""
                                )
                            )

                            if deactivate_subscription(
                                sender_email_value
                            ):

                                st.success(
                                    "Subscription deactivated."
                                )

                                st.rerun()

                    else:

                        if st.button(
                            "▶️ Activate",
                            key=f"activate_{index}_{sender_email}",
                            width='stretch'
                        ):

                            sender_email_value = (
                                subscription.get(
                                    "sender_email",
                                    ""
                                )
                            )

                            if activate_subscription(
                                sender_email_value
                            ):

                                st.success(
                                    "Subscription activated."
                                )

                                st.rerun()


                # ------------------------------------------------
                # DELETE
                # ------------------------------------------------

                with col3:

                    if st.button(
                        "🗑️ Remove Subscription",
                        key=f"delete_subscription_{index}_{sender_email}",
                        width='stretch'
                    ):

                        sender_email_value = (
                            subscription.get(
                                "sender_email",
                                ""
                            )
                        )

                        if delete_subscription(
                            sender_email_value
                        ):

                            st.success(
                                "Subscription removed."
                            )

                            st.rerun()
# ============================================================
# USER FEEDBACK / LEARNING
# ============================================================

elif page == "👤 User Feedback":

    st.markdown(
        '<div class="main-title">User Feedback & Learning</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Review how your corrections help improve the email security system.</div>',
        unsafe_allow_html=True
    )

    history = load_history()

    reviewed = [
        item for item in history
        if item.get("reviewed_by") or item.get("reviewed_at")
    ]

    spam_feedback = sum(
        1 for item in reviewed
        if str(item.get("final_prediction", "")).upper() == "SPAM"
    )

    safe_feedback = sum(
        1 for item in reviewed
        if str(item.get("final_prediction", "")).upper() == "HAM"
    )

    total_feedback = len(reviewed)

    st.info(
        "When you mark an uncertain email as SPAM or SAFE, the decision is "
        "stored as user feedback. This version records the feedback for "
        "future model-improvement work; it does not retrain the ML model automatically."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("👤 Total Corrections", total_feedback)

    with c2:
        st.metric("🚨 Marked as SPAM", spam_feedback)

    with c3:
        st.metric("✅ Marked as SAFE", safe_feedback)

    st.divider()

    if not reviewed:
        st.success("No user feedback has been recorded yet.")
    else:
        st.subheader("📝 Feedback History")

        for index, item in enumerate(reversed(reviewed), start=1):
            prediction = str(
                item.get("final_prediction", "UNKNOWN")
            ).upper()

            icon = "🚨" if prediction == "SPAM" else "✅"
            subject = item.get("subject", "No Subject")
            sender = item.get("sender", "Unknown Sender")
            reviewed_at = item.get("reviewed_at", "Unknown")

            with st.container(border=True):
                st.markdown(
                    f"### {icon} {prediction} — {subject}"
                )
                st.write("**Sender:**", sender)
                st.write("**Reviewed By:**", item.get("reviewed_by", "USER"))
                st.write("**Reviewed At:**", reviewed_at)

                original_prediction = item.get("ml_prediction", "Unknown")
                st.write("**Original ML Prediction:**", original_prediction)

                message_id = item.get("message_id", "")
                if message_id:
                    st.caption(f"Message ID: {message_id}")


# ============================================================
# SETTINGS
# ============================================================

elif page == "📄 Email Security Report":

    st.markdown(
        '<div class="main-title">Email Security Report</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Professional summary of email security, phishing, subscriptions, alerts, and user feedback</div>',
        unsafe_allow_html=True
    )

    report = build_email_security_report()

    st.success("📄 Report generated successfully.")

    st.markdown("### 🛡️ Overall Security Status")
    st.info(report["overall_status"])

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("📨 Total Emails", report["total"])
    with c2:
        st.metric("🚨 Spam", report["spam"])
    with c3:
        st.metric("🎣 High Phishing Risk", report["phishing_high"])
    with c4:
        st.metric("🔔 Unread Alerts", report["unread_alerts"])

    st.divider()

    st.markdown("### 📊 Security Summary")

    summary_data = {
        "Metric": [
            "Spam Rate",
            "Safe Emails",
            "Needs Review",
            "Analysis Errors",
            "High Phishing Risk",
            "Medium Phishing Risk",
            "Suspicious URLs"
        ],
        "Value": [
            f"{report['spam_rate']:.2f}%",
            str(report["ham"]),
            str(report["uncertain"]),
            str(report["errors"]),
            str(report["phishing_high"]),
            str(report["phishing_medium"]),
            str(report["suspicious_urls"])
        ]
    }

    st.table(summary_data)

    st.markdown("### 📬 Subscription Summary")

    sub_data = {
        "Metric": ["Total", "Active", "Inactive"],
        "Value": [
            str(report["subscriptions"]),
            str(report["active_subscriptions"]),
            str(report["inactive_subscriptions"])
        ]
    }

    st.table(sub_data)

    st.markdown("### 👤 User Feedback & Learning")

    feedback_data = {
        "Metric": [
            "Reviewed Emails",
            "Review Rate",
            "Corrections",
            "User Marked SPAM",
            "User Marked SAFE"
        ],
        "Value": [
            str(report["reviewed"]),
            f"{report['review_rate']:.2f}%",
            str(report["corrections"]),
            str(report["feedback_spam"]),
            str(report["feedback_safe"])
        ]
    }

    st.table(feedback_data)

    st.markdown("### 🔔 Security Alerts")

    st.write(
        f"Total alerts: **{report['alerts']}** | "
        f"Unread alerts: **{report['unread_alerts']}**"
    )

    st.markdown("### 📥 Download Report")

    report_html = create_report_html(report)

    st.download_button(
        label="📄 Download Security Report",
        data=report_html,
        file_name="smart_email_security_report.html",
        mime="text/html",
        width="stretch",
        key="download_security_report"
    )

    st.caption(
        "The downloaded HTML report can be opened in any browser "
        "and printed or saved as PDF."
    )

elif page == "⚙️ Settings":

    st.markdown(
        '<div class="main-title">Settings</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Gmail connection and system configuration</div>',
        unsafe_allow_html=True
    )

    settings_tab1, settings_tab2, settings_tab3 = st.tabs([
    "📧 Gmail Connection",
    "⚙️ General Settings",
    "ℹ️ About"
    ])

    with settings_tab1:

        st.subheader("📧 Gmail Integration")

        st.write(
            "Connect your Gmail account to allow the Smart Email System "
            "to analyze your inbox."
        )

        st.divider()

        # ========================================================
        # CHECK GMAIL CONNECTION
        # ========================================================

        BASE_DIR = os.path.dirname(
            os.path.abspath(__file__)
        )

        TOKEN_FILE = os.path.join(
            BASE_DIR,
            "token.json"
        )

        # --------------------------------------------------------
        # CONNECTED
        # --------------------------------------------------------

        if os.path.exists(TOKEN_FILE):

            st.success(
                "🟢 Gmail account is connected."
            )

            st.info(
                "Your Gmail account is ready for email analysis."
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "🔍 Analyze Gmail Emails",
                    width='stretch',
                    key="settings_gmail_analyze"
                ):

                    if model_error:

                        st.error(
                            "ML model is not available. "
                            "Please check the saved_model folder."
                        )

                    else:

                        max_results = st.number_input(
                            "Number of emails to analyze",
                            min_value=1,
                            max_value=50,
                            value=20,
                            step=1,
                            key="gmail_max_results"
                        )

                        with st.spinner(
                            "Connecting to Gmail and analyzing emails..."
                        ):

                            result = analyze_gmail_emails(
                                max_results
                            )

                        if (
                            isinstance(result, dict)
                            and "error" in result
                        ):

                            st.error(
                                "Gmail analysis failed: "
                                + result["error"]
                            )

                        elif not result:

                            st.info(
                                "No emails were found in the Gmail inbox."
                            )

                        else:

                            st.session_state.gmail_results = result

                            saved_count = 0

                            for item in result:

                                if save_email_history(item):

                                    saved_count += 1

                            st.success(
                                f"Successfully analyzed "
                                f"{len(result)} emails. "
                                f"{saved_count} new results "
                                f"saved to history."
                            )

                if st.button(
                    "📬 Full Mailbox Scan",
                    width="stretch",
                    key="full_mailbox_scan"
                ):
                    if model_error:
                        st.error(
                            "ML model is not available. "
                            "Please check the saved_model folder."
                        )
                    else:
                        try:
                            with st.spinner(
                                "Scanning all Inbox messages. "
                                "This may take some time..."
                            ):
                                result = analyze_gmail_emails(scan_all=True)

                            if isinstance(result, dict) and "error" in result:
                                st.error(result["error"])
                            else:
                                st.session_state.gmail_results = result
                                st.success(
                                    f"Full mailbox scan finished. "
                                    f"{len(result)} new messages were processed. "
                                    "Check Email History for saved results."
                                )
                        except Exception as error:
                            st.error(f"Full mailbox scan failed: {error}")

            with col2:

                if st.button(
                    "🔄 Reconnect Gmail",
                    width='stretch',
                    key="reconnect_gmail"
                ):

                    try:

                        os.remove(TOKEN_FILE)

                        st.success(
                            "Gmail connection reset."
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Could not reset Gmail connection: {error}"
                        )

        # --------------------------------------------------------
        # NOT CONNECTED
        # --------------------------------------------------------

        else:

            st.warning(
                "🟡 Gmail account is not connected."
            )

            st.write(
                "Connect your Gmail account before analyzing "
                "emails."
            )

            st.markdown(
                """
                ### 🔐 Gmail Connection

                The Gmail connection uses Google's secure OAuth
                authentication.

                **Steps:**

                1. Click **Connect Gmail**
                2. Sign in to your Gmail account
                3. Allow the required Gmail permissions
                4. Return to Smart Email System
                5. Your account will be ready for analysis
                """
            )

            if st.button(
                "🔗 Connect Gmail",
                width='stretch',
                key="connect_gmail"
            ):

                st.info(
                    "Starting Gmail authentication..."
                )

                try:

                    import subprocess
                    import sys

                    AUTH_FILE = os.path.join(
                        BASE_DIR,
                        "email",
                        "gmail_auth.py"
                    )

                    if not os.path.exists(AUTH_FILE):

                        st.error(
                            "gmail_auth.py was not found at:\n"
                            + AUTH_FILE
                        )

                    else:

                        subprocess.Popen(
                            [
                                sys.executable,
                                AUTH_FILE
                            ],
                            cwd=BASE_DIR
                        )

                        st.success(
                            "Gmail authentication has been started. "
                            "Complete the Google sign-in process, "
                            "then refresh this page."
                        )

                except Exception as error:

                    st.error(
                        f"Unable to start Gmail authentication: {error}"
                    )


        # ========================================================
        # GMAIL ANALYSIS RESULTS
        # ========================================================

        if st.session_state.gmail_results:

            st.divider()

            results = st.session_state.gmail_results

            st.subheader(
                "📊 Gmail Analysis Results"
            )

            spam_count = sum(
                1
                for item in results
                if item.get("final_prediction") == "SPAM"
            )

            ham_count = sum(
                1
                for item in results
                if item.get("final_prediction") == "HAM"
            )

            uncertain_count = sum(
                1
                for item in results
                if item.get("final_prediction") == "UNCERTAIN"
            )

            error_count = sum(
                1
                for item in results
                if item.get("final_prediction") == "ERROR"
            )

            # ============================================================
            # GMAIL ANALYSIS SUMMARY
            # ============================================================

            st.subheader("📊 Gmail Analysis Summary")

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "📨 Total Emails",
                    len(results)
                )

            with c2:
                st.metric(
                    "🚨 Spam Detected",
                    spam_count
                )

            with c3:
                st.metric(
                    "✅ Safe Emails",
                    ham_count
                )

            with c4:
                st.metric(
                    "⚠️ Needs Review",
                    uncertain_count
                )

            st.divider()

            
        with settings_tab2:

            # ============================================================
            # SYSTEM STATUS
            # ============================================================

            st.subheader(
                "🟢 System Status"
            )

            s1, s2, s3 = st.columns(3)

            with s1:

                if model_error:

                    st.error(
                        "❌ ML Model Error"
                    )

                    st.caption(
                        model_error
                    )

                else:

                    st.success(
                        "🟢 ML Model Online"
                    )

                    st.caption(
                        "LinearSVC + TF-IDF"
                    )


            with s2:

                if os.path.exists(
                    HISTORY_FILE
                ):

                    st.success(
                        "🟢 Email History Connected"
                    )

                    st.caption(
                        "History database available"
                    )

                else:

                    st.info(
                        "🟡 Email History Ready"
                    )

                    st.caption(
                        "No history file found yet"
                    )


            with s3:

                if os.path.exists(
                    SUBSCRIPTIONS_FILE
                ):

                    st.success(
                        "🟢 Subscription Data Connected"
                    )

                    st.caption(
                        "Subscription manager available"
                    )

                else:

                    st.info(
                        "🟡 Subscription Data Ready"
                    )

                    st.caption(
                        "No subscription data found yet"
                    )

            st.divider()
        with settings_tab3:

            st.subheader("ℹ️ About Smart Email System")

            st.markdown(
                """
                ### 📧 Smart Email System

                **Machine Learning Based Secondary Spam Mail Detection Using Data Balancing Techniques**

                This system provides an additional layer of protection against
                spam and suspicious emails using machine learning and
                rule-based analysis.

                #### 🤖 Machine Learning
                - **Algorithm:** LinearSVC
                - **Feature Extraction:** TF-IDF
                - **Detection:** Hybrid ML + Rule-Based Analysis

                #### 🛡️ Key Features
                - 📧 Gmail email analysis
                - 🚨 Spam detection
                - ✅ Safe email classification
                - ⚠️ Uncertain email review
                - 📋 Email history
                - 📬 Subscription management
                - 🔄 Automatic Gmail monitoring

                #### 🎯 Project Objective

                To provide a secondary email security layer that helps identify
                spam and suspicious messages more effectively using machine
                learning and data balancing techniques.

                ---

                **Smart Email System**

                *AI-powered secondary email security*
                """
            )    
