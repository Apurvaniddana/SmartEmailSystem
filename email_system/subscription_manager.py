import json
import os
from datetime import datetime


# ============================================================
# SMART EMAIL SYSTEM
# STEP 7 - SUBSCRIPTION MANAGER
# ============================================================


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)


SUBSCRIPTION_FILE = os.path.join(
    DATA_DIR,
    "subscriptions.json"
)


# ------------------------------------------------------------
# CREATE DATA DIRECTORY
# ------------------------------------------------------------

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ------------------------------------------------------------
# LOAD SUBSCRIPTIONS
# ------------------------------------------------------------

def load_subscriptions():

    if not os.path.exists(
        SUBSCRIPTION_FILE
    ):

        return []

    try:

        with open(
            SUBSCRIPTION_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):

            return data

        return []

    except (
        json.JSONDecodeError,
        OSError
    ):

        return []


# ------------------------------------------------------------
# SAVE SUBSCRIPTIONS
# ------------------------------------------------------------

def save_subscriptions(
    subscriptions
):

    try:

        with open(
            SUBSCRIPTION_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                subscriptions,
                file,
                indent=4,
                ensure_ascii=False
            )

        return True

    except OSError as error:

        print(
            f"Error saving subscriptions: {error}"
        )

        return False


# ------------------------------------------------------------
# EXTRACT EMAIL ADDRESS
# ------------------------------------------------------------

def extract_email(sender):

    if not sender:

        return ""

    sender = sender.strip()

    if "<" in sender and ">" in sender:

        start = sender.find("<") + 1

        end = sender.find(">")

        return sender[
            start:end
        ].strip()

    return sender


# ------------------------------------------------------------
# ADD OR UPDATE SUBSCRIPTION
# ------------------------------------------------------------

def add_subscription(
    sender,
    subject,
    subscription_type,
    unsubscribe_url=None,
    indicators=None
):

    subscriptions = load_subscriptions()

    sender_email = extract_email(
        sender
    )

    if indicators is None:

        indicators = []

    existing_subscription = None

    # --------------------------------------------------------
    # FIND EXISTING SUBSCRIPTION
    # --------------------------------------------------------

    for subscription in subscriptions:

        existing_email = subscription.get(
            "sender_email",
            ""
        )

        if (
            existing_email.lower()
            == sender_email.lower()
        ):

            existing_subscription = subscription

            break

    # --------------------------------------------------------
    # UPDATE EXISTING
    # --------------------------------------------------------

    if existing_subscription:

        # Update current subject
        existing_subscription[
            "subject"
        ] = subject

        # Update type
        existing_subscription[
            "type"
        ] = subscription_type

        # Update last seen time
        existing_subscription[
            "last_seen"
        ] = datetime.now().isoformat()

        # Update unsubscribe URL
        if unsubscribe_url:

            existing_subscription[
                "unsubscribe_url"
            ] = unsubscribe_url

        # Update indicators
        existing_subscription[
            "indicators"
        ] = indicators

        # Reactivate if email is detected again
        existing_subscription[
            "status"
        ] = "ACTIVE"

        save_subscriptions(
            subscriptions
        )

        return existing_subscription

    # --------------------------------------------------------
    # CREATE NEW
    # --------------------------------------------------------

    now = datetime.now().isoformat()

    new_subscription = {

        "sender":
            sender,

        "sender_email":
            sender_email,

        "subject":
            subject,

        "type":
            subscription_type,

        "unsubscribe_url":
            unsubscribe_url,

        "indicators":
            indicators,

        "status":
            "ACTIVE",

        "first_seen":
            now,

        "last_seen":
            now
    }

    subscriptions.append(
        new_subscription
    )

    save_subscriptions(
        subscriptions
    )

    return new_subscription


# ------------------------------------------------------------
# DISPLAY SUBSCRIPTIONS
# ------------------------------------------------------------

def display_subscriptions():

    subscriptions = load_subscriptions()

    print()

    print("=" * 70)

    print("SUBSCRIPTION MANAGER")

    print("=" * 70)

    if not subscriptions:

        print(
            "No subscriptions found."
        )

        print("=" * 70)

        return

    print(
        f"Total subscriptions : "
        f"{len(subscriptions)}"
    )

    print()

    for index, subscription in enumerate(
        subscriptions,
        start=1
    ):

        print("-" * 70)

        print(
            f"Subscription {index}"
        )

        print(
            "Sender          : "
            + str(
                subscription.get(
                    "sender",
                    "Unknown"
                )
            )
        )

        print(
            "Email           : "
            + str(
                subscription.get(
                    "sender_email",
                    "Unknown"
                )
            )
        )

        print(
            "Type            : "
            + str(
                subscription.get(
                    "type",
                    "Unknown"
                )
            )
        )

        print(
            "Subject         : "
            + str(
                subscription.get(
                    "subject",
                    "Unknown"
                )
            )
        )

        print(
            "Status          : "
            + str(
                subscription.get(
                    "status",
                    "UNKNOWN"
                )
            )
        )

        unsubscribe_url = subscription.get(
            "unsubscribe_url"
        )

        if unsubscribe_url:

            print(
                "Unsubscribe URL : "
                + str(
                    unsubscribe_url
                )
            )

        indicators = subscription.get(
            "indicators",
            []
        )

        if indicators:

            print(
                "Indicators      : "
                + ", ".join(
                    indicators
                )
            )

        print(
            "First Seen      : "
            + str(
                subscription.get(
                    "first_seen",
                    ""
                )
            )
        )

        print(
            "Last Seen       : "
            + str(
                subscription.get(
                    "last_seen",
                    ""
                )
            )
        )

    print("-" * 70)

    print("=" * 70)


# ------------------------------------------------------------
# DEACTIVATE SUBSCRIPTION
# ------------------------------------------------------------

def deactivate_subscription(
    sender_email
):

    subscriptions = load_subscriptions()

    found = False

    sender_email = (
        sender_email or ""
    ).strip().lower()

    for subscription in subscriptions:

        existing_email = (
            subscription.get(
                "sender_email",
                ""
            )
            .strip()
            .lower()
        )

        if existing_email == sender_email:

            subscription[
                "status"
            ] = "INACTIVE"

            subscription[
                "deactivated_at"
            ] = datetime.now().isoformat()

            found = True

    if found:

        save_subscriptions(
            subscriptions
        )

    return found


# ------------------------------------------------------------
# DELETE SUBSCRIPTION
# ------------------------------------------------------------

def delete_subscription(
    sender_email
):

    subscriptions = load_subscriptions()

    updated_subscriptions = []

    deleted = False

    sender_email = (
        sender_email or ""
    ).strip().lower()

    for subscription in subscriptions:

        existing_email = (
            subscription.get(
                "sender_email",
                ""
            )
            .strip()
            .lower()
        )

        if existing_email == sender_email:

            deleted = True

        else:

            updated_subscriptions.append(
                subscription
            )

    if deleted:

        save_subscriptions(
            updated_subscriptions
        )

    return deleted


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    print("=" * 70)

    print("SMART EMAIL SYSTEM")

    print("SUBSCRIPTION MANAGER")

    print("=" * 70)

    display_subscriptions()


# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------

if __name__ == "__main__":

    main()