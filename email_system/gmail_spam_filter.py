import os
import re
import html
import base64
import pickle

from bs4 import BeautifulSoup

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# ============================================================
# SMART EMAIL SYSTEM
# GMAIL HYBRID SPAM FILTER
# ============================================================


# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
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
# 2. GMAIL PERMISSIONS
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]


# ============================================================
# 3. CHECK REQUIRED FILES
# ============================================================

if not os.path.exists(MODEL_FILE):

    print("ERROR: ML model not found!")

    print(
        "Expected:",
        MODEL_FILE
    )

    exit()


if not os.path.exists(VECTORIZER_FILE):

    print("ERROR: TF-IDF vectorizer not found!")

    print(
        "Expected:",
        VECTORIZER_FILE
    )

    exit()


if not os.path.exists(TOKEN_FILE):

    print("ERROR: token.json not found!")

    print(
        "Expected:",
        TOKEN_FILE
    )

    exit()


# ============================================================
# 4. LOAD ML MODEL
# ============================================================

print("Loading ML model...")

try:

    with open(
        MODEL_FILE,
        "rb"
    ) as file:

        model = pickle.load(file)

except Exception as error:

    print("ERROR loading ML model:")
    print(error)

    exit()


print(
    "ML model loaded successfully!"
)


# ============================================================
# 5. LOAD TF-IDF VECTORIZER
# ============================================================

print(
    "Loading TF-IDF vectorizer..."
)

try:

    with open(
        VECTORIZER_FILE,
        "rb"
    ) as file:

        vectorizer = pickle.load(file)

except Exception as error:

    print(
        "ERROR loading TF-IDF vectorizer:"
    )

    print(error)

    exit()


print(
    "TF-IDF vectorizer loaded successfully!"
)


# ============================================================
# 6. CONNECT TO GMAIL
# ============================================================

def get_gmail_service():

    try:

        credentials = (
            Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES
            )
        )

        service = build(
            "gmail",
            "v1",
            credentials=credentials
        )

        return service

    except Exception as error:

        print(
            "ERROR connecting to Gmail:"
        )

        print(error)

        exit()


# ============================================================
# 7. GET EMAIL HEADER
# ============================================================

def get_header(
    headers,
    header_name
):

    for header in headers:

        name = header.get(
            "name",
            ""
        )

        if name.lower() == header_name.lower():

            return header.get(
                "value",
                ""
            )

    return ""


# ============================================================
# 8. DECODE GMAIL BODY
# ============================================================

def decode_body(data):

    if not data:

        return ""

    try:

        decoded = (
            base64.urlsafe_b64decode(
                data
            )
            .decode(
                "utf-8",
                errors="ignore"
            )
        )

        return decoded

    except Exception:

        return ""


# ============================================================
# 9. EXTRACT EMAIL BODY
# ============================================================

def extract_body(payload):

    if not payload:

        return ""


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


    # --------------------------------------------------------
    # Prefer plain text
    # --------------------------------------------------------

    for part in parts:

        mime_type = part.get(
            "mimeType",
            ""
        )

        if mime_type == "text/plain":

            result = extract_body(
                part
            )

            if result:

                return result


    # --------------------------------------------------------
    # Then try HTML
    # --------------------------------------------------------

    for part in parts:

        mime_type = part.get(
            "mimeType",
            ""
        )

        if mime_type == "text/html":

            result = extract_body(
                part
            )

            if result:

                return result


    # --------------------------------------------------------
    # Recursively search all parts
    # --------------------------------------------------------

    for part in parts:

        result = extract_body(
            part
        )

        if result:

            return result


    return ""


# ============================================================
# 10. CLEAN EMAIL CONTENT
# ============================================================

def clean_text(text):

    if not text:

        return ""


    # Decode HTML entities

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
        text,
        flags=re.IGNORECASE
    )


    text = re.sub(
        r"www\.\S+",
        " ",
        text,
        flags=re.IGNORECASE
    )


    # Remove email addresses

    text = re.sub(
        r"\b[\w.+-]+@[\w.-]+\.\w+\b",
        " ",
        text
    )


    # Normalize whitespace

    text = re.sub(
        r"\s+",
        " ",
        text
    )


    return text.strip()


# ============================================================
# 11. SPAM RULES
# ============================================================
#
# IMPORTANT:
#
# We intentionally DO NOT treat generic words such as:
#
#     free
#     offer
#     earn
#     stipend
#     selected
#     click
#     congratulations
#
# as strong spam indicators.
#
# These words are common in legitimate emails.
#
# ============================================================

spam_patterns = {

    # --------------------------------------------------------
    # VERY STRONG SPAM COMBINATIONS
    # --------------------------------------------------------

    r"\bwon\b.*\bprize\b":
        5,

    r"\bprize\b.*\bwon\b":
        5,

    r"\bclaim\b.*\bprize\b":
        5,

    r"\bclaim\b.*\bmoney\b":
        5,

    r"\bfree\b.*\bgift\b":
        5,

    r"\bfree\b.*\bvoucher\b":
        5,

    r"\bearn money\b":
        5,

    r"\bmake money\b":
        5,

    r"\baccount has been compromised\b":
        5,

    r"\bverify your account\b":
        5,

    r"\bverify\b.*\baccount\b":
        4,

    r"\burgent\b.*\baccount\b":
        4,

    r"\burgent\b.*\bverify\b":
        4,

    r"\blimited time\b.*\boffer\b":
        4,


    # --------------------------------------------------------
    # STRONG SPAM COMBINATIONS
    # --------------------------------------------------------

    r"\bclick here\b.*\bclaim\b":
        4,

    r"\bclick here\b.*\bprize\b":
        4,

    r"\bclick the link\b.*\bverify\b":
        4,

    r"\bfree vacation\b":
        4,

    r"\bspecial bonus\b":
        3,

    r"\bexclusive offer\b":
        3,

    r"\binvestment opportunity\b":
        3,

    r"\bprize pool\b":
        3,

    r"\bcongratulations\b.*\bwon\b":
        4,

    r"\bcongratulations\b.*\bprize\b":
        4,


    # --------------------------------------------------------
    # MONEY-BASED INDICATORS
    # --------------------------------------------------------

    r"\$\s?\d{3,}":
        3,

    r"₹\s?\d{4,}":
        2,

    r"\b\d+\s*(million|lakhs?|crores?)\b":
        3
}


# ============================================================
# 12. CALCULATE RULE SCORE
# ============================================================

def calculate_spam_score(
    text
):

    score = 0

    indicators = []


    text_lower = text.lower()


    for pattern, points in spam_patterns.items():

        try:

            if re.search(
                pattern,
                text_lower
            ):

                score += points

                indicators.append(
                    pattern
                )

        except re.error:

            continue


    return (
        score,
        indicators
    )


# ============================================================
# 13. HYBRID CLASSIFIER
# ============================================================

def classify_email(
    subject,
    body
):

    # --------------------------------------------------------
    # Clean subject
    # --------------------------------------------------------

    subject_clean = clean_text(
        subject
    )


    # --------------------------------------------------------
    # Clean body
    # --------------------------------------------------------

    body_clean = clean_text(
        body
    )


    # --------------------------------------------------------
    # Combine subject + body
    # --------------------------------------------------------

    combined_text = (
        subject_clean
        + " "
        + body_clean
    )


    # --------------------------------------------------------
    # ML FEATURES
    # --------------------------------------------------------

    features = vectorizer.transform(
        [combined_text]
    )


    # --------------------------------------------------------
    # ML PREDICTION
    # --------------------------------------------------------

    ml_prediction = model.predict(
        features
    )[0]


    # --------------------------------------------------------
    # ML DECISION SCORE
    # --------------------------------------------------------

    try:

        ml_score = float(
            model.decision_function(
                features
            )[0]
        )

    except Exception:

        ml_score = 0.0


    # --------------------------------------------------------
    # RULE ENGINE
    # --------------------------------------------------------

    (
        rule_score,
        indicators
    ) = calculate_spam_score(
        combined_text
    )


    # ========================================================
    # FINAL HYBRID DECISION
    # ========================================================

    # --------------------------------------------------------
    # Case 1:
    # Strong rule evidence
    # --------------------------------------------------------

    if rule_score >= 5:

        final_prediction = "SPAM"


    # --------------------------------------------------------
    # Case 2:
    # Moderate rule evidence + ML agrees
    # --------------------------------------------------------

    elif (
        rule_score >= 3
        and ml_score > 0
    ):

        final_prediction = "SPAM"


    # --------------------------------------------------------
    # Case 3:
    # ML predicts spam with meaningful confidence
    # --------------------------------------------------------

    elif (
        str(
            ml_prediction
        ).lower()
        == "spam"
    ):

        if ml_score >= 0.50:

            final_prediction = "SPAM"

        else:

            final_prediction = "HAM"


    # --------------------------------------------------------
    # Case 4:
    # Otherwise HAM
    # --------------------------------------------------------

    else:

        final_prediction = "HAM"


    # ========================================================
    # CONFIDENCE
    # ========================================================

    if final_prediction == "SPAM":

        if rule_score >= 7:

            confidence = (
                "HIGH CONFIDENCE SPAM"
            )

        elif rule_score >= 5:

            confidence = (
                "LIKELY SPAM"
            )

        elif ml_score >= 1.0:

            confidence = (
                "HIGH CONFIDENCE SPAM"
            )

        elif ml_score >= 0.50:

            confidence = (
                "LIKELY SPAM"
            )

        else:

            confidence = (
                "UNCERTAIN SPAM"
            )

    else:

        if (
            ml_score <= -0.20
            and rule_score <= 2
        ):

            confidence = (
                "HIGH CONFIDENCE HAM"
            )

        else:

            confidence = "HAM"


    return (
        ml_prediction,
        ml_score,
        rule_score,
        indicators,
        final_prediction,
        confidence
    )


# ============================================================
# 14. APPLY SPAM LABEL
# ============================================================

def mark_as_spam(
    service,
    message_id
):

    try:

        service.users().messages().modify(

            userId="me",

            id=message_id,

            body={
                "addLabelIds": [
                    "SPAM"
                ]
            }

        ).execute()


        return True


    except Exception as error:

        print(
            "ERROR applying Gmail SPAM label:"
        )

        print(error)

        return False


# ============================================================
# 15. GET GMAIL EMAILS
# ============================================================

def get_messages(
    service,
    max_results=10
):

    try:

        result = (
            service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=max_results
            )
            .execute()
        )


        return result.get(
            "messages",
            []
        )


    except Exception as error:

        print(
            "ERROR getting Gmail messages:"
        )

        print(error)

        return []


# ============================================================
# 16. PROCESS ONE EMAIL
# ============================================================

def process_email(
    service,
    message,
    number
):

    try:

        # ----------------------------------------------------
        # Get full email
        # ----------------------------------------------------

        email_data = (
            service.users()
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


        # ----------------------------------------------------
        # Headers
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # Body
        # ----------------------------------------------------

        body = extract_body(
            payload
        )


        # ----------------------------------------------------
        # Classify
        # ----------------------------------------------------

        (
            ml_prediction,
            ml_score,
            rule_score,
            indicators,
            final_prediction,
            confidence
        ) = classify_email(
            subject,
            body
        )


        # ====================================================
        # DISPLAY RESULT
        # ====================================================

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

        print(
            "Spam Indicators :",
            indicators
        )

        print(
            f"FINAL PREDICTION: "
            f"{final_prediction}"
        )

        print(
            f"CONFIDENCE      : "
            f"{confidence}"
        )


        # ====================================================
        # GMAIL ACTION
        # ====================================================

        if (
            final_prediction == "SPAM"
            and confidence in [
                "HIGH CONFIDENCE SPAM",
                "LIKELY SPAM"
            ]
        ):

            success = mark_as_spam(
                service,
                message["id"]
            )


            if success:

                print(
                    "GMAIL ACTION    : "
                    "SPAM LABEL APPLIED"
                )

                return "SPAM"


            else:

                print(
                    "GMAIL ACTION    : "
                    "FAILED"
                )

                return "ERROR"


        elif (
            final_prediction == "SPAM"
            and confidence == "UNCERTAIN SPAM"
        ):

            print(
                "GMAIL ACTION    : "
                "NO ACTION - "
                "UNCERTAIN SPAM"
            )

            return "UNCERTAIN"


        else:

            print(
                "GMAIL ACTION    : "
                "NO ACTION - HAM"
            )

            return "HAM"


    except Exception as error:

        print()

        print(
            f"Email {number} ERROR:"
        )

        print(error)

        return "ERROR"


# ============================================================
# 17. MAIN PROGRAM
# ============================================================

def main():

    print()

    print(
        "==================================="
    )

    print(
        "      SMART EMAIL SYSTEM"
    )

    print(
        "   GMAIL HYBRID SPAM FILTER"
    )

    print(
        "==================================="
    )

    print()


    # --------------------------------------------------------
    # Connect Gmail
    # --------------------------------------------------------

    service = get_gmail_service()


    # --------------------------------------------------------
    # Get emails
    # --------------------------------------------------------

    messages = get_messages(
        service,
        max_results=10
    )


    print(
        f"Emails found: {len(messages)}"
    )


    if not messages:

        print(
            "No emails found."
        )

        return


    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

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

        result = process_email(
            service,
            message,
            number
        )


        if result == "HAM":

            ham_count += 1


        elif result == "SPAM":

            spam_count += 1


        elif result == "UNCERTAIN":

            uncertain_count += 1


        elif result == "ERROR":

            error_count += 1


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()

    print(
        "==================================="
    )

    print(
        "       FILTERING COMPLETE"
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
        f"Uncertain spam   : {uncertain_count}"
    )

    print(
        f"Errors           : {error_count}"
    )

    print(
        f"Total processed  : "
        f"{ham_count + spam_count + uncertain_count + error_count}"
    )

    print(
        "==================================="
    )


# ============================================================
# 18. START PROGRAM
# ============================================================

if __name__ == "__main__":

    main()