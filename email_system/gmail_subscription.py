import os
import sys
import base64
import re

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# ============================================================
# SMART EMAIL SYSTEM
# STEP 9 - GMAIL SUBSCRIPTION INTEGRATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]


# ------------------------------------------------------------
# PROJECT MODULE PATH
# ------------------------------------------------------------

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


from subscription_detector import (
    detect_subscription,
    detect_promotional
)

from subscription_manager import (
    add_subscription,
    display_subscriptions
)


# ------------------------------------------------------------
# GMAIL AUTHENTICATION
# ------------------------------------------------------------

def get_gmail_service():

    if not os.path.exists(TOKEN_FILE):

        print()
        print("ERROR: token.json not found.")
        print()
        print(
            "Run your Gmail authentication program first."
        )

        return None

    try:

        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

        service = build(
            "gmail",
            "v1",
            credentials=credentials
        )

        return service

    except Exception as error:

        print()
        print(
            f"Gmail authentication error: {error}"
        )

        return None


# ------------------------------------------------------------
# DECODE GMAIL MESSAGE
# ------------------------------------------------------------

def decode_message_data(data):

    if not data:
        return ""

    try:

        decoded = base64.urlsafe_b64decode(
            data
        )

        return decoded.decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:

        return ""


# ------------------------------------------------------------
# EXTRACT BODY
# ------------------------------------------------------------

def extract_body(payload):

    body = ""

    if not payload:
        return body

    mime_type = payload.get(
        "mimeType",
        ""
    )

    payload_body = payload.get(
        "body",
        {}
    )

    data = payload_body.get(
        "data"
    )

    if data:

        body += decode_message_data(
            data
        )

    parts = payload.get(
        "parts",
        []
    )

    for part in parts:

        body += extract_body(
            part
        )

    return body


# ------------------------------------------------------------
# GET HEADER
# ------------------------------------------------------------

def get_header(
    headers,
    name
):

    for header in headers:

        if (
            header.get(
                "name",
                ""
            ).lower()
            == name.lower()
        ):

            return header.get(
                "value",
                ""
            )

    return ""


# ------------------------------------------------------------
# GET GMAIL EMAILS
# ------------------------------------------------------------

def get_emails(
    service,
    max_results=20
):

    try:

        result = service.users().messages().list(
            userId="me",
            maxResults=max_results
        ).execute()

        messages = result.get(
            "messages",
            []
        )

        emails = []

        for message in messages:

            message_id = message.get(
                "id"
            )

            email_data = service.users().messages().get(
                userId="me",
                id=message_id,
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

            emails.append({

                "id":
                    message_id,

                "sender":
                    sender,

                "subject":
                    subject,

                "date":
                    date,

                "message":
                    body
            })

        return emails

    except Exception as error:

        print()
        print(
            f"Error reading Gmail: {error}"
        )

        return []


# ------------------------------------------------------------
# PROCESS EMAIL
# ------------------------------------------------------------

def process_email(
    index,
    email
):

    sender = email.get(
        "sender",
        ""
    )

    subject = email.get(
        "subject",
        ""
    )

    message = email.get(
        "message",
        ""
    )

    date = email.get(
        "date",
        ""
    )

    print()
    print(
        f"Processing Email {index}..."
    )

    print(
        f"From    : {sender}"
    )

    print(
        f"Subject : {subject}"
    )

    print(
        f"Date    : {date}"
    )

    # --------------------------------------------------------
    # SUBSCRIPTION DETECTION
    # --------------------------------------------------------

    subscription_result = detect_subscription(
        subject,
        message,
        sender
    )

    promotional_result = detect_promotional(
        subject,
        message
    )

    print()
    print(
        "=" * 60
    )

    print(
        "SUBSCRIPTION ANALYSIS"
    )

    print(
        "=" * 60
    )

    print(
        f"Sender        : {sender}"
    )

    print(
        f"Subject       : {subject}"
    )

    # --------------------------------------------------------
    # SUBSCRIPTION
    # --------------------------------------------------------

    if subscription_result[
        "is_subscription"
    ]:

        print(
            "Type          : "
            "NEWSLETTER / SUBSCRIPTION"
        )

        print(
            "Subscription  : YES"
        )

        indicators = subscription_result[
            "indicators"
        ]

        print(
            "Indicators    : "
            + ", ".join(indicators)
        )

        if subscription_result[
            "unsubscribe_available"
        ]:

            print(
                "Unsubscribe   : AVAILABLE"
            )

            print(
                "Unsubscribe URL : "
                + str(
                    subscription_result[
                        "unsubscribe_link"
                    ]
                )
            )

        else:

            print(
                "Unsubscribe   : NOT FOUND"
            )

        # ----------------------------------------------------
        # SAVE SUBSCRIPTION
        # ----------------------------------------------------

        add_subscription(

            sender=sender,

            subject=subject,

            subscription_type=
                subscription_result[
                    "type"
                ],

            unsubscribe_url=
                subscription_result[
                    "unsubscribe_link"
                ],

            indicators=
                subscription_result[
                    "indicators"
                ]
        )

    # --------------------------------------------------------
    # PROMOTIONAL
    # --------------------------------------------------------

    elif promotional_result[
        "is_promotional"
    ]:

        print(
            "Type          : PROMOTIONAL"
        )

        print(
            "Subscription  : POSSIBLE"
        )

        print(
            "Indicators    : "
            + ", ".join(
                promotional_result[
                    "indicators"
                ]
            )
        )

    # --------------------------------------------------------
    # NORMAL
    # --------------------------------------------------------

    else:

        print(
            "Type          : NORMAL EMAIL"
        )

        print(
            "Subscription  : NO"
        )

    print(
        "=" * 60
    )

    return subscription_result


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    print()
    print("=" * 60)
    print("SMART EMAIL SYSTEM")
    print("GMAIL SUBSCRIPTION DETECTOR")
    print("=" * 60)

    service = get_gmail_service()

    if service is None:

        return

    print()
    print(
        "Reading Gmail inbox..."
    )

    emails = get_emails(
        service,
        max_results=20
    )

    print()

    print(
        f"Emails found: {len(emails)}"
    )

    if not emails:

        print(
            "No emails found."
        )

        return

    subscription_count = 0
    promotional_count = 0
    normal_count = 0

    # --------------------------------------------------------
    # PROCESS EMAILS
    # --------------------------------------------------------

    for index, email in enumerate(
        emails,
        start=1
    ):

        result = process_email(
            index,
            email
        )

        if result[
            "is_subscription"
        ]:

            subscription_count += 1

        else:

            promotional_result = detect_promotional(
                email.get(
                    "subject",
                    ""
                ),
                email.get(
                    "message",
                    ""
                )
            )

            if promotional_result[
                "is_promotional"
            ]:

                promotional_count += 1

            else:

                normal_count += 1

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SUBSCRIPTION CLASSIFICATION SUMMARY")
    print("=" * 60)

    print(
        f"Subscriptions : {subscription_count}"
    )

    print(
        f"Promotional   : {promotional_count}"
    )

    print(
        f"Normal        : {normal_count}"
    )

    print(
        f"Total         : {len(emails)}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # SAVED SUBSCRIPTIONS
    # --------------------------------------------------------

    print()
    print(
        "SAVED SUBSCRIPTIONS"
    )

    display_subscriptions()


# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------

if __name__ == "__main__":

    main()