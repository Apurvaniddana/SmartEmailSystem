import os
import re
import html
import base64
import pickle

from bs4 import BeautifulSoup
from email_history import record_email
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "saved_model",
    "improved_linear_svc.pkl"
)

VECTORIZER_FILE = os.path.join(
    BASE_DIR,
    "saved_model",
    "improved_tfidf_vectorizer.pkl"
)


# ============================================================
# CHECK MODEL FILES
# ============================================================

print("Checking model files...")

if not os.path.exists(MODEL_FILE):
    print("ERROR: Model file not found:")
    print(MODEL_FILE)
    raise FileNotFoundError(MODEL_FILE)

print("Model file found.")

if not os.path.exists(VECTORIZER_FILE):
    print("ERROR: Vectorizer file not found:")
    print(VECTORIZER_FILE)
    raise FileNotFoundError(VECTORIZER_FILE)


print("Vectorizer file found.")


# ============================================================
# LOAD ML MODEL
# ============================================================

print()
print("Loading ML model...")

with open(MODEL_FILE, "rb") as f:
    model = pickle.load(f)

print("ML model loaded successfully!")


# ============================================================
# LOAD TF-IDF VECTORIZER
# ============================================================

print("Loading TF-IDF vectorizer...")

with open(VECTORIZER_FILE, "rb") as f:
    vectorizer = pickle.load(f)

print("TF-IDF vectorizer loaded successfully!")


# ============================================================
# GMAIL SERVICE
# ============================================================

def get_gmail_service():

    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(
            "token.json not found. Run:\n"
            "python email\\gmail_auth.py"
        )

    credentials = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        ["https://www.googleapis.com/auth/gmail.modify"]
    )

    # --------------------------------------------------------
    # Refresh expired access token
    # --------------------------------------------------------

    if credentials.expired and credentials.refresh_token:

        try:
            credentials.refresh(Request())

        except Exception as error:

            print()
            print("GMAIL AUTHENTICATION ERROR")
            print("-----------------------------------")
            print(error)
            print()
            print("Run:")
            print("python email\\gmail_auth.py")
            print()
            raise

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )


# ============================================================
# GET HEADER
# ============================================================

def get_header(headers, name):

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
# DECODE BODY
# ============================================================

def decode_body(data):

    if not data:
        return ""

    try:

        return base64.urlsafe_b64decode(
            data
        ).decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:

        return ""


# ============================================================
# EXTRACT EMAIL BODY
# ============================================================

def extract_body(payload):

    # --------------------------------------------------------
    # Direct body
    # --------------------------------------------------------

    body_data = payload.get(
        "body",
        {}
    ).get(
        "data"
    )

    if body_data:

        return decode_body(
            body_data
        )


    # --------------------------------------------------------
    # Multipart email
    # --------------------------------------------------------

    parts = payload.get(
        "parts",
        []
    )


    # --------------------------------------------------------
    # Prefer plain text
    # --------------------------------------------------------

    for part in parts:

        if part.get(
            "mimeType"
        ) == "text/plain":

            result = extract_body(
                part
            )

            if result:
                return result


    # --------------------------------------------------------
    # Try HTML / nested parts
    # --------------------------------------------------------

    for part in parts:

        result = extract_body(
            part
        )

        if result:
            return result


    return ""


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    # --------------------------------------------------------
    # HTML entities
    # --------------------------------------------------------

    text = html.unescape(
        text
    )


    # --------------------------------------------------------
    # Remove HTML
    # --------------------------------------------------------

    try:

        soup = BeautifulSoup(
            text,
            "html.parser"
        )

        text = soup.get_text(
            separator=" "
        )

    except Exception:

        pass


    # --------------------------------------------------------
    # Remove URLs
    # --------------------------------------------------------

    text = re.sub(
        r"https?://\S+",
        " ",
        text
    )

    text = re.sub(
        r"www\.\S+",
        " ",
        text
    )


    # --------------------------------------------------------
    # Remove excessive spaces
    # --------------------------------------------------------

    text = re.sub(
        r"\s+",
        " ",
        text
    )


    return text.strip()


# ============================================================
# ML CLASSIFICATION
# ============================================================

def classify_email(subject, body):

    subject = clean_text(
        subject
    )

    body = clean_text(
        body
    )


    # --------------------------------------------------------
    # Combine subject + body
    # --------------------------------------------------------

    combined_text = (
        subject
        + " "
        + body
    )


    # --------------------------------------------------------
    # TF-IDF
    # --------------------------------------------------------

    features = vectorizer.transform(
        [combined_text]
    )


    # --------------------------------------------------------
    # ML Prediction
    # --------------------------------------------------------

    prediction = model.predict(
        features
    )[0]


    # --------------------------------------------------------
    # Decision Function Score
    # --------------------------------------------------------

    decision_score = model.decision_function(
        features
    )[0]


    # --------------------------------------------------------
    # Convert prediction
    # --------------------------------------------------------

    if str(
        prediction
    ).lower() == "spam":

        final_prediction = "SPAM"

    else:

        final_prediction = "HAM"


    return (
        final_prediction,
        float(decision_score)
    )


# ============================================================
# RULE BASED ANALYSIS
# ============================================================

def rule_analysis(
    sender,
    subject,
    body
):

    text = (
        subject
        + " "
        + body
    ).lower()


    # ========================================================
    # TRUSTED SENDERS
    # ========================================================

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


    sender_lower = sender.lower()


    trusted_sender = any(
        domain in sender_lower
        for domain in trusted_domains
    )


    # ========================================================
    # RULES
    # ========================================================

    spam_rules = [

        (
            r"\bfree\b",
            1
        ),

        (
            r"\boffer\b",
            2
        ),

        (
            r"\bbonus\b",
            2
        ),

        (
            r"\bdeal\b",
            2
        ),

        (
            r"\bdiscount\b",
            2
        ),

        (
            r"\bpromotion\b",
            1
        ),

        (
            r"\bprize\b",
            3
        ),

        (
            r"\breward\b",
            3
        ),

        (
            r"\bwon\b",
            4
        ),

        (
            r"\bwinner\b",
            4
        ),

        (
            r"\blottery\b",
            5
        ),

        (
            r"\bcash prize\b",
            5
        ),

        (
            r"\bclaim your prize\b",
            6
        ),

        (
            r"\bclaim your money\b",
            6
        ),

        (
            r"\bclick here to claim\b",
            6
        ),

        (
            r"\bverify your password\b",
            6
        ),

        (
            r"\baccount suspended\b",
            6
        ),

        (
            r"\burgent\b",
            3
        )
    ]


    score = 0
    indicators = []


    # ========================================================
    # CHECK RULES
    # ========================================================

    for pattern, points in spam_rules:

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):

            score += points

            indicators.append(
                pattern
            )


    # ========================================================
    # EXCESSIVE EXCLAMATION
    # ========================================================

    if text.count("!") >= 5:

        score += 2

        indicators.append(
            "excessive_exclamation"
        )


    # ========================================================
    # MONEY AMOUNT
    # ========================================================

    money_pattern = (
        r"[$₹€£]\s?\d+"
    )

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
# HYBRID FINAL DECISION
# ============================================================

def final_decision(
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
        subject
        + " "
        + body
    ).lower()


    # ========================================================
    # VERY STRONG SPAM PHRASES
    # ========================================================

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


    # ========================================================
    # DECISION 1
    # VERY STRONG ML SPAM
    # ========================================================

    if (
        ml_prediction == "SPAM"
        and ml_score >= 0.50
    ):

        return "SPAM"


    # ========================================================
    # DECISION 2
    # VERY STRONG SPAM CONTENT
    #
    # For trusted senders, require both:
    #   strong spam content
    #   AND ML supports spam
    # ========================================================

    if strong_spam:

        if not trusted_sender:

            return "SPAM"

        if (
            trusted_sender
            and ml_prediction == "SPAM"
            and ml_score >= 0.10
        ):

            return "SPAM"


    # ========================================================
    # DECISION 3
    # TRUSTED SENDER
    #
    # A trusted sender + HAM should remain HAM.
    # This prevents words like:
    # free, offer, bonus, promotion
    # from incorrectly sending legitimate emails to Spam.
    # ========================================================

    if (
        trusted_sender
        and ml_prediction == "HAM"
    ):

        return "HAM"


    # ========================================================
    # DECISION 4
    # STRONG HAM
    # ========================================================

    if (
        ml_prediction == "HAM"
        and ml_score <= -0.20
    ):

        return "HAM"


    # ========================================================
    # DECISION 5
    # STRONG SPAM
    # ========================================================

    if (
        ml_prediction == "SPAM"
        and ml_score >= 0.20
    ):

        return "SPAM"


    # ========================================================
    # DECISION 6
    # RULE SCORE
    #
    # Only use rules aggressively for non-trusted senders.
    # ========================================================

    if not trusted_sender:

        if rule_score >= 6:

            return "SPAM"


    # ========================================================
    # DECISION 7
    # MODERATE HAM
    # ========================================================

    if (
        ml_prediction == "HAM"
        and ml_score <= -0.10
    ):

        return "HAM"


    # ========================================================
    # NOT ENOUGH EVIDENCE
    # ========================================================

    return "UNCERTAIN"


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(score):

    """
    Display-oriented confidence estimate.

    This is NOT a calibrated probability.
    """

    confidence = 50 + (
        abs(score) * 50
    )

    confidence = min(
        confidence,
        99.99
    )

    return confidence


# ============================================================
# GMAIL ACTION
# ============================================================

def gmail_action(
    service,
    message_id,
    final_prediction
):

    # --------------------------------------------------------
    # HAM
    # --------------------------------------------------------

    if final_prediction == "HAM":

        return "NO ACTION - HAM"


    # --------------------------------------------------------
    # UNCERTAIN
    # --------------------------------------------------------

    if final_prediction == "UNCERTAIN":

        return "NO ACTION - UNCERTAIN"


    # --------------------------------------------------------
    # SPAM
    # --------------------------------------------------------

    if final_prediction == "SPAM":

        try:

            service.users().messages().modify(

                userId="me",

                id=message_id,

                body={
                    "addLabelIds": ["SPAM"]
                }

            ).execute()


            return "MOVED TO SPAM"


        except Exception as error:

            return (
                "SPAM ACTION ERROR: "
                + str(error)
            )


    return "NO ACTION"


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Gmail service
    # --------------------------------------------------------

    service = get_gmail_service()


    # --------------------------------------------------------
    # Get inbox emails
    # --------------------------------------------------------

    results = service.users().messages().list(

        userId="me",

        labelIds=["INBOX"],

        maxResults=20

    ).execute()


    messages = results.get(
        "messages",
        []
    )


    # ========================================================
    # HEADER
    # ========================================================

    print()

    print(
        "==================================="
    )

    print(
        "SMART EMAIL SYSTEM"
    )

    print(
        "GMAIL SPAM DETECTION"
    )

    print(
        "HYBRID ML CLASSIFIER"
    )

    print(
        "==================================="
    )


    print()

    print(
        f"Emails found: {len(messages)}"
    )


    # ========================================================
    # COUNTERS
    # ========================================================

    ham_count = 0

    spam_count = 0

    uncertain_count = 0

    error_count = 0


    # ========================================================
    # PROCESS EMAILS
    # ========================================================

    for number, message in enumerate(
        messages,
        start=1
    ):

        try:

            print()

            print(
                f"## Processing Email {number}..."
            )


            # ------------------------------------------------
            # Get complete email
            # ------------------------------------------------

            email_data = (
                service
                .users()
                .messages()
                .get(

                    userId="me",

                    id=message["id"],

                    format="full"

                )
                .execute()
            )


            payload = email_data.get(
                "payload",
                {}
            )


            headers = payload.get(
                "headers",
                []
            )


            # ------------------------------------------------
            # Headers
            # ------------------------------------------------

            sender = get_header(
                headers,
                "From"
            )


            subject = get_header(
                headers,
                "Subject"
            )


            date = get_header(
                headers,
                "Date"
            )


            # ------------------------------------------------
            # Body
            # ------------------------------------------------

            body = extract_body(
                payload
            )


            # ------------------------------------------------
            # ML classification
            # ------------------------------------------------

            ml_prediction, ml_score = classify_email(
                subject,
                body
            )


            # ------------------------------------------------
            # Rule analysis
            # ------------------------------------------------

            trusted_sender, rule_score, indicators = (
                rule_analysis(
                    sender,
                    subject,
                    body
                )
            )


            # ------------------------------------------------
            # Hybrid decision
            # ------------------------------------------------

            final_prediction = final_decision(

                ml_prediction,

                ml_score,

                sender,

                subject,

                body
            )


            # ------------------------------------------------
            # Confidence
            # ------------------------------------------------

            confidence = calculate_confidence(
                ml_score
            )


            # ------------------------------------------------
            # Gmail action
            # ------------------------------------------------

            action = gmail_action(

                service,

                message["id"],

                final_prediction

            )


            # =================================================
            # STEP 12 - EMAIL HISTORY
            # =================================================

            history_saved = record_email(

                message_id=message["id"],

                sender=sender,

                subject=subject,

                date=date,

                ml_prediction=ml_prediction,

                ml_score=ml_score,

                confidence=confidence,

                final_prediction=final_prediction,

                gmail_action=action

            )

            if history_saved:
                print("HISTORY         : SAVED")
            else:
                print("HISTORY         : ALREADY EXISTS")


            # =================================================
            # COUNTERS
            # =================================================

            if final_prediction == "HAM":

                ham_count += 1

            elif final_prediction == "SPAM":

                spam_count += 1

            else:

                uncertain_count += 1


            # =================================================
            # DISPLAY
            # =================================================

            print()

            print(
                f"Email {number}"
            )


            print(
                f"From            : {sender}"
            )


            print(
                f"Subject         : {subject}"
            )


            print(
                f"Date            : {date}"
            )


            print(
                f"ML Prediction   : {ml_prediction}"
            )


            print(
                f"ML Score        : {ml_score:.4f}"
            )


            print(
                f"Confidence      : {confidence:.2f}%"
            )


            print(
                f"Trusted Sender  : "
                f"{'YES' if trusted_sender else 'NO'}"
            )


            print(
                f"Rule Score      : {rule_score}"
            )


            if indicators:

                print(
                    "Spam Indicators : "
                    + ", ".join(indicators)
                )

            else:

                print(
                    "Spam Indicators : None"
                )


            print(
                f"FINAL PREDICTION: "
                f"{final_prediction}"
            )


            print(
                f"GMAIL ACTION    : "
                f"{action}"
            )


            print(
                "-----------------------------------"
            )


        except Exception as error:

            error_count += 1


            print()

            print(
                f"Email {number} ERROR:"
            )


            print(
                error
            )


            print(
                "-----------------------------------"
            )


    # ========================================================
    # CLASSIFICATION SUMMARY
    # ========================================================

    total_processed = (
        ham_count
        + spam_count
        + uncertain_count
    )


    print()

    print(
        "==================================="
    )

    print(
        "CLASSIFICATION SUMMARY"
    )

    print(
        "==================================="
    )


    print(
        f"HAM emails       : {ham_count}"
    )


    print(
        f"SPAM emails      : {spam_count}"
    )


    print(
        f"UNCERTAIN emails : {uncertain_count}"
    )


    print(
        f"Errors           : {error_count}"
    )


    print(
        f"Total processed  : {total_processed}"
    )


    print(
        "==================================="
    )


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    main()