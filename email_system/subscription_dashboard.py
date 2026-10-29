import os
import sys


# ============================================================
# SMART EMAIL SYSTEM
# STEP 10 - SUBSCRIPTION DASHBOARD
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


from subscription_manager import (
    load_subscriptions,
    save_subscriptions,
    deactivate_subscription,
    delete_subscription
)


# ------------------------------------------------------------
# DISPLAY HEADER
# ------------------------------------------------------------

def show_header():

    print()
    print("=" * 75)
    print("             SMART EMAIL SYSTEM")
    print("             SUBSCRIPTION DASHBOARD")
    print("=" * 75)


# ------------------------------------------------------------
# DISPLAY ALL SUBSCRIPTIONS
# ------------------------------------------------------------

def show_subscriptions():

    subscriptions = load_subscriptions()

    print()
    print("=" * 75)
    print("                 SAVED SUBSCRIPTIONS")
    print("=" * 75)

    if not subscriptions:

        print("No subscriptions found.")

        return subscriptions

    print(
        f"Total subscriptions: {len(subscriptions)}"
    )

    for index, subscription in enumerate(
        subscriptions,
        start=1
    ):

        print()
        print("-" * 75)

        print(
            f"[{index}] "
            f"{subscription.get('sender', 'Unknown')}"
        )

        print(
            f"    Email       : "
            f"{subscription.get('sender_email', 'Unknown')}"
        )

        print(
            f"    Type        : "
            f"{subscription.get('type', 'Unknown')}"
        )

        print(
            f"    Subject     : "
            f"{subscription.get('subject', 'Unknown')}"
        )

        print(
            f"    Status      : "
            f"{subscription.get('status', 'UNKNOWN')}"
        )

        unsubscribe_url = subscription.get(
            "unsubscribe_url"
        )

        if unsubscribe_url:

            print(
                f"    Unsubscribe : AVAILABLE"
            )

            print(
                f"    URL         : "
                f"{unsubscribe_url}"
            )

        else:

            print(
                "    Unsubscribe : NOT AVAILABLE"
            )

    print()
    print("=" * 75)

    return subscriptions


# ------------------------------------------------------------
# DEACTIVATE SUBSCRIPTION
# ------------------------------------------------------------

def deactivate():

    subscriptions = load_subscriptions()

    if not subscriptions:

        print(
            "\nNo subscriptions available."
        )

        return

    show_subscriptions()

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
        subscriptions
    ):

        print(
            "Invalid subscription number."
        )

        return

    selected = subscriptions[
        choice - 1
    ]

    sender_email = selected.get(
        "sender_email",
        ""
    )

    if not sender_email:

        print(
            "Sender email not found."
        )

        return

    success = deactivate_subscription(
        sender_email
    )

    if success:

        print()
        print(
            "Subscription status changed "
            "to INACTIVE."
        )

    else:

        print(
            "Subscription could not be updated."
        )


# ------------------------------------------------------------
# DELETE SUBSCRIPTION
# ------------------------------------------------------------

def delete():

    subscriptions = load_subscriptions()

    if not subscriptions:

        print(
            "\nNo subscriptions available."
        )

        return

    show_subscriptions()

    try:

        choice = int(
            input(
                "\nEnter subscription number "
                "to delete: "
            )
        )

    except ValueError:

        print(
            "Invalid number."
        )

        return

    if choice < 1 or choice > len(
        subscriptions
    ):

        print(
            "Invalid subscription number."
        )

        return

    selected = subscriptions[
        choice - 1
    ]

    sender_email = selected.get(
        "sender_email",
        ""
    )

    confirm = input(
        f"\nDelete {sender_email}? (y/n): "
    ).strip().lower()

    if confirm != "y":

        print(
            "Delete cancelled."
        )

        return

    updated = []

    deleted = False

    for subscription in subscriptions:

        if (
            subscription.get(
                "sender_email",
                ""
            ).lower()
            == sender_email.lower()
        ):

            deleted = True

        else:

            updated.append(
                subscription
            )

    if deleted:

        save_subscriptions(
            updated
        )

        print(
            "\nSubscription deleted."
        )

    else:

        print(
            "\nSubscription not found."
        )


# ------------------------------------------------------------
# SHOW ACTIVE SUBSCRIPTIONS
# ------------------------------------------------------------

def show_active():

    subscriptions = load_subscriptions()

    active = []

    for subscription in subscriptions:

        if (
            subscription.get(
                "status",
                ""
            ).upper()
            == "ACTIVE"
        ):

            active.append(
                subscription
            )

    print()
    print("=" * 75)
    print("                 ACTIVE SUBSCRIPTIONS")
    print("=" * 75)

    if not active:

        print(
            "No active subscriptions."
        )

        return

    for index, subscription in enumerate(
        active,
        start=1
    ):

        print()

        print(
            f"{index}. "
            f"{subscription.get('sender', 'Unknown')}"
        )

        print(
            f"   Email: "
            f"{subscription.get('sender_email', '')}"
        )

        print(
            f"   Status: "
            f"{subscription.get('status', '')}"
        )

        url = subscription.get(
            "unsubscribe_url"
        )

        if url:

            print(
                f"   Unsubscribe URL: {url}"
            )

    print()
    print("=" * 75)


# ------------------------------------------------------------
# MAIN DASHBOARD
# ------------------------------------------------------------

def main():

    while True:

        show_header()

        print()
        print("1. View all subscriptions")
        print("2. View active subscriptions")
        print("3. Deactivate subscription")
        print("4. Delete subscription")
        print("5. Exit")

        print()

        choice = input(
            "Enter your choice: "
        ).strip()

        if choice == "1":

            show_subscriptions()

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "2":

            show_active()

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "3":

            deactivate()

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "4":

            delete()

            input(
                "\nPress Enter to continue..."
            )

        elif choice == "5":

            print()
            print(
                "Exiting Subscription Dashboard..."
            )

            break

        else:

            print()
            print(
                "Invalid choice."
            )

            input(
                "Press Enter to continue..."
            )


# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------

if __name__ == "__main__":

    main()