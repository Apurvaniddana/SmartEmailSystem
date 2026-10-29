import os
import sys
import subprocess


# ============================================================
# SMART EMAIL SYSTEM
# STEP 13 - MAIN SYSTEM INTEGRATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

EMAIL_SYSTEM_DIR = os.path.join(
    BASE_DIR,
    "email_system"
)


# ============================================================
# RUN A MODULE
# ============================================================

def run_module(filename):

    filepath = os.path.join(
        EMAIL_SYSTEM_DIR,
        filename
    )

    if not os.path.exists(filepath):

        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(f"File not found: {filepath}")

        input("\nPress Enter to continue...")

        return

    print()
    print("=" * 60)
    print(f"Starting {filename}")
    print("=" * 60)
    print()

    try:

        result = subprocess.run(
            [
                sys.executable,
                filepath
            ],
            cwd=BASE_DIR
        )

        if result.returncode != 0:

            print()
            print(
                f"{filename} exited with "
                f"code {result.returncode}"
            )

    except Exception as error:

        print()
        print(
            f"Error running {filename}: {error}"
        )

    input("\nPress Enter to continue...")


# ============================================================
# MAIN MENU
# ============================================================

def main():

    while True:

        os.system(
            "cls"
            if os.name == "nt"
            else "clear"
        )

        print("=" * 70)
        print("                 SMART EMAIL SYSTEM")
        print("=" * 70)

        print()
        print("1. Gmail Spam Detection")
        print("2. Subscription Manager")
        print("3. Subscription Dashboard")
        print("4. Email History")
        print("5. Unsubscribe Manager")
        print("6. Exit")

        print()
        choice = input(
            "Enter your choice: "
        ).strip()

        # ----------------------------------------------------
        # OPTION 1
        # ----------------------------------------------------

        if choice == "1":

            run_module(
                "gmail_classifier.py"
            )

        # ----------------------------------------------------
        # OPTION 2
        # ----------------------------------------------------

        elif choice == "2":

            run_module(
                "subscription_manager.py"
            )

        # ----------------------------------------------------
        # OPTION 3
        # ----------------------------------------------------

        elif choice == "3":

            run_module(
                "subscription_dashboard.py"
            )

        # ----------------------------------------------------
        # OPTION 4
        # ----------------------------------------------------

        elif choice == "4":

            run_module(
                "email_history.py"
            )

        # ----------------------------------------------------
        # OPTION 5
        # ----------------------------------------------------

        elif choice == "5":

            run_module(
                "unsubscribe_manager.py"
            )

        # ----------------------------------------------------
        # OPTION 6
        # ----------------------------------------------------

        elif choice == "6":

            print()
            print("=" * 70)
            print("              Exiting Smart Email System...")
            print("=" * 70)

            break

        # ----------------------------------------------------
        # INVALID CHOICE
        # ----------------------------------------------------

        else:

            print()
            print(
                "Invalid choice."
            )

            input(
                "\nPress Enter to continue..."
            )


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    main()