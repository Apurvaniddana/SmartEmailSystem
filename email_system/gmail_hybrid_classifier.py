import os
import re
import html
import base64
import pickle

from bs4 import BeautifulSoup

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


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
# LOAD ML MODEL
# ============================================================

print("Loading ML model...")

with open(MODEL_FILE, "rb") as file:
    model = pickle.load(file)

print("ML model loaded successfully!")


print("Loading TF-IDF vectorizer...")

with open(VECTORIZER_FILE, "rb") as file:
    vectorizer = pickle.load(file)

print("TF-IDF vectorizer loaded successfully!")


# ============================================================
# GMAIL AUTHENTICATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]


def get_gmail_service():

    credentials = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        SCOPES
    )

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )


# ============================================================
# GET EMAIL HEADER
# ============================================================

def get_header(headers, name):

    for header in headers:

        if header.get("name", "").lower() == name.lower():

            return header.get(
                "value",
                ""
            )

    return ""


# ============================================================
# DECODE EMAIL BODY
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

    body = payload.get(
        "body",
        {}
    )

    data = body.get(
        "data"
    )

    if data:

        return decode_body(
            data
        )


    # --------------------------------------------------------
    # Multipart email
    # --------------------------------------------------------

    parts = payload.get(
        "parts",
        []
    )


    # First look for plain text

    for part in parts:

        if part.get(
            "mimeType"
        ) == "text/plain":

            result = extract_body(
                part
            )

            if result:

                return result


    # Then check nested HTML/other parts

    for part in parts:

        result = extract_body(
            part
        )

        if result:

            return result


    return ""


# ============================================================
# CLEAN EMAIL TEXT
# ============================================================

def clean_text(text):

    if not text:

        return ""


    # Convert HTML entities

    text = html.unescape(
        text
    )


    # Remove HTML tags

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


    # Remove URLs

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


    # Remove excessive whitespace

    text = re.sub(
        r"\s+",
        " ",
        text
    )


    return text.strip()


# ============================================================
# SPAM PATTERNS
# ============================================================

spam_patterns = {

    # Strong spam indicators

    r"\bwon\b": 2,

    r"\bwin\b": 2,

    r"\bprize\b": 2,

    r"\breward\b": 2,

    r"\bfree gift\b": 3,

    r"\bclaim\b": 2,

    r"\bcongratulations\b": 2,

    r"\bcash\b": 2,

    r"\bmoney\b": 2,

    r"\bearn money\b": 3,

    r"\bmake money\b": 3,

    r"\baccount has been compromised\b": 3,

    r"\bverify your account\b": 2,

    r"\burgent\b": 2,

    r"\blimited time\b": 2,

    r"\bspecial offer\b": 2,

    r"\bexclusive offer\b": 2,

    r"\binvestment opportunity\b": 2,

    r"\bprize pool\b": 2,

    r"\bbonus\b": 2,

    r"\bfree\b": 2,

    r"\boffer\b": 1,

    r"\bdeal\b": 1,

    r"\bdiscount\b": 1,

    r"\bstipend\b": 1,

    r"\bearn\b": 1,

    r"\bselected\b": 1,

    r"\b₹\s?\d+": 2,

    r"\$\s?\d+": 2,


    # Weaker indicators

    r"\bclick here\b": 1,

    r"\bclick the link\b": 1,

    r"\bclick\b": 1
}


# ============================================================
# RULE ENGINE
# ============================================================

def calculate_spam_score(text):

    score = 0

    indicators = []


    text_lower = text.lower()


    for pattern, points in spam_patterns.items():

        if re.search(
            pattern,
            text_lower
        ):

            score += points

            indicators.append(
                pattern
            )


    return score, indicators


# ============================================================
# HYBRID CLASSIFIER
# ============================================================

def classify_email(subject, body):

    # --------------------------------------------------------
    # Clean subject and body
    # --------------------------------------------------------

    subject_clean = clean_text(
        subject
    )

    body_clean = clean_text(
        body
    )


    # Combine

    combined_text = (
        subject_clean
        + " "
        + body_clean
    )


    # --------------------------------------------------------
    # ML PREDICTION
    # --------------------------------------------------------

    features = vectorizer.transform(
        [combined_text]
    )


    ml_prediction = model.predict(
        features
    )[0]


    ml_score = model.decision_function(
        features
    )[0]


    # --------------------------------------------------------
    # RULE SCORE
    # --------------------------------------------------------

    rule_score, indicators = calculate_spam_score(
        combined_text
    )


    # --------------------------------------------------------
    # FINAL HYBRID DECISION
    # --------------------------------------------------------
    #
    # Strong rule evidence:
    # Rule score >= 5 -> SPAM
    #
    # Moderate rule evidence:
    # Only override ML when ML is already
    # leaning toward SPAM.
    #
    # ML itself predicts SPAM -> SPAM
    #
    # Otherwise -> HAM
    # --------------------------------------------------------

    if rule_score >= 5:

        final_prediction = "SPAM"


    elif rule_score >= 3 and ml_score > 0:

        final_prediction = "SPAM"


    elif str(
        ml_prediction
    ).lower() == "spam":

        final_prediction = "SPAM"


    else:

        final_prediction = "HAM"


    return (
        ml_prediction,
        ml_score,
        rule_score,
        indicators,
        final_prediction
    )


# ============================================================
# MAIN GMAIL PROCESS
# ============================================================

def main():

    service = get_gmail_service()


    # --------------------------------------------------------
    # GET LATEST 10 EMAILS
    # --------------------------------------------------------

    results = service.users().messages().list(

        userId="me",

        labelIds=["INBOX"],

        maxResults=10

    ).execute()


    messages = results.get(
        "messages",
        []
    )


    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    print()

    print(
        "==================================="
    )

    print(
        "SMART EMAIL SYSTEM"
    )

    print(
        "HYBRID GMAIL SPAM DETECTION"
    )

    print(
        "==================================="
    )


    print()

    print(
        f"Emails found: {len(messages)}"
    )


    # --------------------------------------------------------
    # PROCESS EACH EMAIL
    # --------------------------------------------------------

    for number, message in enumerate(
        messages,
        start=1
    ):

        try:

            # Get complete email

            email_data = service.users().messages().get(

                userId="me",

                id=message["id"],

                format="full"

            ).execute()


            payload = email_data.get(
                "payload",
                {}
            )


            headers = payload.get(
                "headers",
                []
            )


            # ------------------------------------------------
            # Extract information
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


            body = extract_body(
                payload
            )


            # ------------------------------------------------
            # Classify
            # ------------------------------------------------

            (
                ml_prediction,
                ml_score,
                rule_score,
                indicators,
                final_prediction

            ) = classify_email(

                subject,

                body

            )


            # ------------------------------------------------
            # Display
            # ------------------------------------------------

            print()

            print(
                "-----------------------------------"
            )

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
                f"ML Prediction   : "
                f"{str(ml_prediction).upper()}"
            )


            print(
                f"ML Score        : "
                f"{ml_score:.4f}"
            )


            print(
                f"Rule Score      : "
                f"{rule_score}"
            )


            if indicators:

                print(
                    "Spam Indicators :",
                    indicators
                )

            else:

                print(
                    "Spam Indicators : []"
                )


            print(
                f"FINAL PREDICTION: "
                f"{final_prediction}"
            )


            print(
                "-----------------------------------"
            )


        except Exception as error:

            print()

            print(
                f"Email {number} ERROR:"
            )

            print(
                error
            )


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    main()