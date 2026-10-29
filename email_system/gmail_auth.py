import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]

PROJECT_FOLDER = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CREDENTIALS_FILE = os.path.join(
    PROJECT_FOLDER,
    "credentials.json"
)

TOKEN_FILE = os.path.join(
    PROJECT_FOLDER,
    "token.json"
)


def authenticate_gmail():

    credentials = None

    # Check existing token
    if os.path.exists(TOKEN_FILE):

        try:
            credentials = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES
            )

        except Exception:
            credentials = None


    # Existing valid token
    
    # Check whether the existing token has the required Gmail scope
    required_scope = "https://www.googleapis.com/auth/gmail.modify"

    if credentials and credentials.valid:
        existing_scopes = credentials.scopes or []

        if required_scope in existing_scopes:
            print()
            print("===================================")
            print("GMAIL AUTHENTICATION SUCCESSFUL")
            print("===================================")
            print()
            print("Existing token has Gmail modify permission.")
            return credentials

        else:
            print("Existing token does not have Gmail modify permission.")
            print("Removing old token to request authorization again.")

            try:
                os.remove(TOKEN_FILE)
            except OSError:
                pass

            credentials = None



    # Remove invalid token
    if credentials and credentials.expired:

        print()
        print("Existing token is expired.")
        print("Removing old token...")

        try:
            os.remove(TOKEN_FILE)
        except OSError:
            pass

        credentials = None


    # New authentication
    if credentials is None:

        print()
        print("===================================")
        print("STARTING GMAIL AUTHENTICATION")
        print("===================================")

        if not os.path.exists(CREDENTIALS_FILE):

            raise FileNotFoundError(
                "credentials.json not found:\n"
                + CREDENTIALS_FILE
            )


        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )


        print()
        print("Opening Google authorization...")
        print("Please complete Gmail authorization in the browser.")
        print()


        credentials = flow.run_local_server(
            host="127.0.0.1",
            port=0,
            open_browser=True,
            authorization_prompt_message=(
                "Please visit this URL to authorize this application: {url}"
            ),
            success_message=(
                "Gmail authentication successful. "
                "You can close this browser window."
            )
        )


    # Save token
    with open(
        TOKEN_FILE,
        "w",
        encoding="utf-8"
    ) as token:

        token.write(
            credentials.to_json()
        )


    print()
    print("===================================")
    print("GMAIL AUTHENTICATION SUCCESSFUL")
    print("===================================")
    print()
    print("Token saved at:")
    print(TOKEN_FILE)
    print()

    return credentials


if __name__ == "__main__":

    authenticate_gmail()