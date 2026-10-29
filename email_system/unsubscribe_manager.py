import os
import sys
import webbrowser


# ============================================================
# SMART EMAIL SYSTEM
# STEP 11 - UNSUBSCRIBE MANAGER
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


from subscription_manager import (
    load_subscriptions,
    save_subscriptions
)


# ------------------------------------------------------------
# DISPLAY UNSUBSCRIBE OPTIONS
# ------------------------------------------------------------

def show_unsubscribe_options():

    subscriptions = load_subscriptions()

    available = []

    for subscription in subscriptions:

        url = subscription.get(
            "unsubscribe_url"
        )

        status = subscription.get(
            "status",
            "UNKNOWN"
        )

        if url and status.upper() == "ACTIVE":

            available.append(
                subscription
            )

    print()
    print("=" * 75)
    print("              UNSUBSCRIBE MANAGER")
    print("=" * 75)

    if not available:

        print()
        print(
            "No active subscriptions with "
            "unsubscribe links found."
        )

        print("=" * 75)

        return

    print(
        f"Available unsubscribe options: "
        f"{len(available)}"
    )

    print()

    for index, subscription in enumerate(
        available,
        start=1
    ):

        print("-" * 75)

        print(
            f"[{index}] "
            f"{subscription.get('sender', 'Unknown')}"
        )

        print(
            f"    Email : "
            f"{subscription.get('sender_email', '')}"
        )

        print(
            f"    URL   : "
            f"{subscription.get('unsubscribe_url', '')}"
        )

    print("-" * 75)


# ------------------------------------------------------------
# OPEN UNSUBSCRIBE PAGE
# ------------------------------------------------------------

def open_unsubscribe_page():

    subscriptions = load_subscriptions()

    available = []

    for subscription in subscriptions:

        url = subscription.get(
            "unsubscribe_url"
        )

        status = subscription.get(
            "status",
            "UNKNOWN"
        )

        if url and status.upper() == "ACTIVE":

            available.append(
                subscription
            )

    if not available:

        print(
            "\nNo unsubscribe links available."
        )

        return

    show_unsubscribe_options()

    try:

        choice = int(
            input(
                "\nEnter subscription number: "
            )
        )

    except ValueError:

        print(
            "Invalid number."
        )

        return

    if choice < 1 or choice > len(
        available
    ):

        print(
            "Invalid subscription number."
        )

        return

    selected = available[
        choice - 1
    ]

    sender = selected.get(
        "sender",
        "Unknown"
    )

    url = selected.get(
        "unsubscribe_url"
    )

    print()
    print(
        f"Opening unsubscribe page for:"
    )

    print(
        sender
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "Complete the unsubscribe process "
        "on the website."
    )

    print()

    webbrowser.open(url)

    print(
        "Browser opened."
    )

    print()
    print(
        "After successfully unsubscribing, "
        "you can mark this subscription as "
        "INACTIVE from the dashboard."
    )


# ------------------------------------------------------------
# MARK AS UNSUBSCRIBED
# ------------------------------------------------------------

def mark_unsubscribed():

    subscriptions = load_subscriptions()

    available = []

    for subscription in subscriptions:

        if subscription.get(
            "status",
            ""
        ).upper() == "ACTIVE":

            available.append(
                subscription
            )

    if not available:

        print(
            "\nNo active subscriptions."
        )

        return

    print()
    print("=" * 75)
    print("MARK SUBSCRIPTION AS UNSUBSCRIBED")
    print("=" * 75)

    for index, subscription in enumerate(
        available,
        start=1
    ):

        print(
            f"{index}. "
            f"{subscription.get('sender_email', '')}"
        )

    try:

        choice = int(
            input(
                "\nEnter subscription number: "
            )
        )

    except ValueError:

        print(
            "Invalid number."
        )

        return

    if choice < 1 or choice > len(
        available
    ):

        print(
            "Invalid subscription number."
        )

        return

    selected = available[
        choice - 1
    ]

    selected_email = selected.get(
        "sender_email",
        ""
    )

    confirm = input(
        f"\nConfirm that you unsubscribed "
        f"from {selected_email}? (y/n): "
    ).strip().lower()

    if confirm != "y":

        print(
            "Operation cancelled."
        )

        return

    for subscription in subscriptions:

        if (
            subscription.get(
                "sender_email",
                ""
            ).lower()
            == selected_email.lower()
        ):

            subscription["status"] = (
                "INACTIVE"
            )

    save_subscriptions(
        subscriptions
    )

    print()
    print(
        "Subscription marked as INACTIVE."
    )


# ------------------------------------------------------------
# MAIN MENU
# ------------------------------------------------------------

def main():

    while True:

        print()
        print("=" * 75)
        print("             SMART EMAIL SYSTEM")
        print("             UNSUBSCRIBE MANAGER")
        print("=" * 75)

        print()
        print("1. View unsubscribe links")
        print("2. Open unsubscribe page")
        print("3. Mark as unsubscribed")
        print("4. Exit")

        print()

        choice = input(
            "Enter your choice: "
        ).strip()

        if choice == "1":

            show_unsubscribe_options()

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "2":

            open_unsubscribe_page()

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "3":

            mark_unsubscribed()

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "4":

            print(
                "\nExiting Unsubscribe Manager..."
            )

            break

        else:

            print(
                "\nInvalid choice."
            )


# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------

if __name__ == "__main__":

    main()