import os
import base64

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# ============================================================
# GMAIL PERMISSION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_FOLDER = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


TOKEN_FILE = os.path.join(
    PROJECT_FOLDER,
    "token.json"
)


# ============================================================
# GMAIL SERVICE
# ============================================================

def get_gmail_service():

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


# ============================================================
# GET HEADER
# ============================================================

def get_header(headers, name):

    for header in headers:

        if header["name"].lower() == name.lower():

            return header["value"]

    return ""


# ============================================================
# GET EMAIL BODY
# ============================================================

def get_email_body(payload):

    # --------------------------------------------------------
    # Direct body
    # --------------------------------------------------------

    if (
        "body" in payload
        and payload["body"].get("data")
    ):

        data = payload["body"]["data"]

        try:

            return base64.urlsafe_b64decode(
                data
            ).decode(
                "utf-8",
                errors="ignore"
            )

        except Exception:

            return ""


    # --------------------------------------------------------
    # Multipart email
    # --------------------------------------------------------

    if "parts" in payload:

        for part in payload["parts"]:

            body = get_email_body(part)

            if body:

                return body


    return ""


# ============================================================
# READ EMAILS
# ============================================================

def read_emails(max_results=20):

    service = get_gmail_service()


    # --------------------------------------------------------
    # Get latest Inbox emails
    # --------------------------------------------------------

    results = service.users().messages().list(

        userId="me",

        labelIds=[
            "INBOX"
        ],

        maxResults=max_results

    ).execute()


    messages = results.get(
        "messages",
        []
    )


    print("\n===================================")
    print("GMAIL EMAIL READER")
    print("===================================")

    print(
        f"\nEmails found: {len(messages)}\n"
    )


    # --------------------------------------------------------
    # Read each email
    # --------------------------------------------------------

    emails = []


    for number, message in enumerate(
        messages,
        start=1
    ):

        try:

            message_data = (
                service.users()
                .messages()
                .get(

                    userId="me",

                    id=message["id"],

                    format="full"

                )
                .execute()
            )


            payload = message_data.get(
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


            body = get_email_body(
                payload
            )


            email_data = {

                "id": message["id"],

                "sender": sender,

                "subject": subject,

                "date": date,

                "body": body

            }


            emails.append(
                email_data
            )


            print("-----------------------------------")

            print(
                f"Email {number}"
            )

            print(
                f"From   : {sender}"
            )

            print(
                f"Subject: {subject}"
            )

            print(
                f"Date   : {date}"
            )

            print(
                f"Message:\n{body[:500]}"
            )

            print("-----------------------------------")


        except Exception as error:

            print(
                f"\nERROR reading Email {number}:"
            )

            print(error)


    return emails


# ============================================================
# TEST READER
# ============================================================

if __name__ == "__main__":

    read_emails(
        max_results=20
    )