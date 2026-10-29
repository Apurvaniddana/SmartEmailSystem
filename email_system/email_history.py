import os
import json
from datetime import datetime


# ============================================================
# SMART EMAIL SYSTEM
# STEP 12 - EMAIL HISTORY & RECOVERY
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


HISTORY_FILE = os.path.join(
    DATA_DIR,
    "email_history.json"
)


# ------------------------------------------------------------
# CREATE DATA DIRECTORY
# ------------------------------------------------------------

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ------------------------------------------------------------
# LOAD EMAIL HISTORY
# ------------------------------------------------------------

def load_history():

    if not os.path.exists(HISTORY_FILE):

        return []


    try:

        with open(
            HISTORY_FILE,
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
# SAVE EMAIL HISTORY
# ------------------------------------------------------------

def save_history(history):

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                history,
                file,
                indent=4,
                ensure_ascii=False
            )


        return True


    except OSError as error:

        print(
            f"Error saving email history: {error}"
        )

        return False


# ------------------------------------------------------------
# RECORD EMAIL
# ------------------------------------------------------------

def record_email(
    message_id,
    sender,
    subject,
    date,
    ml_prediction,
    ml_score,
    confidence,
    final_prediction,
    gmail_action
):

    history = load_history()


    # --------------------------------------------------------
    # CHECK DUPLICATE
    # --------------------------------------------------------

    for item in history:

        if str(
            item.get(
                "message_id",
                ""
            )
        ) == str(message_id):

            return False


    # --------------------------------------------------------
    # CREATE RECORD
    # --------------------------------------------------------

    record = {

        "message_id": message_id,

        "sender": sender,

        "subject": subject,

        "date": date,

        "ml_prediction": ml_prediction,

        "ml_score": float(
            ml_score
        ),

        "confidence": float(
            confidence
        ),

        "final_prediction": final_prediction,

        "gmail_action": gmail_action,

        "processed_at":
            datetime.now().isoformat()

    }


    # --------------------------------------------------------
    # ADD RECORD
    # --------------------------------------------------------

    history.append(
        record
    )


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    return save_history(
        history
    )


# ------------------------------------------------------------
# DISPLAY HISTORY
# ------------------------------------------------------------

def display_history():

    history = load_history()


    print()

    print(
        "=" * 80
    )

    print(
        "                    EMAIL HISTORY"
    )

    print(
        "=" * 80
    )


    if not history:

        print()

        print(
            "No email history found."
        )

        print()

        print(
            "=" * 80
        )

        return


    print(
        f"Total records : {len(history)}"
    )


    for index, item in enumerate(
        history,
        start=1
    ):

        print()

        print(
            "-" * 80
        )


        print(
            f"Record {index}"
        )


        print(
            f"Message ID    : "
            f"{item.get('message_id', '')}"
        )


        print(
            f"Sender        : "
            f"{item.get('sender', '')}"
        )


        print(
            f"Subject       : "
            f"{item.get('subject', '')}"
        )


        print(
            f"Date          : "
            f"{item.get('date', '')}"
        )


        print(
            f"ML Prediction : "
            f"{item.get('ml_prediction', '')}"
        )


        print(
            f"ML Score      : "
            f"{item.get('ml_score', '')}"
        )


        print(
            f"Confidence    : "
            f"{item.get('confidence', '')}%"
        )


        print(
            f"Final Result  : "
            f"{item.get('final_prediction', '')}"
        )


        print(
            f"Gmail Action  : "
            f"{item.get('gmail_action', '')}"
        )


        print(
            f"Processed At  : "
            f"{item.get('processed_at', '')}"
        )


    print()

    print(
        "=" * 80
    )


# ------------------------------------------------------------
# HISTORY SUMMARY
# ------------------------------------------------------------

def history_summary():

    history = load_history()


    print()

    print(
        "=" * 70
    )

    print(
        "                 HISTORY SUMMARY"
    )

    print(
        "=" * 70
    )


    if not history:

        print(
            "No email history found."
        )

        print(
            "=" * 70
        )

        return


    ham_count = 0

    spam_count = 0

    uncertain_count = 0


    for item in history:

        result = item.get(
            "final_prediction",
            ""
        )


        if result == "HAM":

            ham_count += 1


        elif result == "SPAM":

            spam_count += 1


        elif result == "UNCERTAIN":

            uncertain_count += 1


    total = len(history)


    print(
        f"Total emails     : {total}"
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


    if total > 0:

        print(
            f"HAM percentage   : "
            f"{(ham_count / total) * 100:.2f}%"
        )

        print(
            f"SPAM percentage  : "
            f"{(spam_count / total) * 100:.2f}%"
        )


    print(
        "=" * 70
    )


# ------------------------------------------------------------
# SEARCH HISTORY
# ------------------------------------------------------------

def search_history():

    history = load_history()


    if not history:

        print()

        print(
            "No email history found."
        )

        return


    print()

    search_text = input(
        "Enter sender or subject to search: "
    ).strip().lower()


    if not search_text:

        print(
            "Search text cannot be empty."
        )

        return


    results = []


    for item in history:

        sender = str(
            item.get(
                "sender",
                ""
            )
        ).lower()


        subject = str(
            item.get(
                "subject",
                ""
            )
        ).lower()


        if (
            search_text in sender
            or search_text in subject
        ):

            results.append(
                item
            )


    print()

    print(
        "=" * 80
    )

    print(
        "                    SEARCH RESULTS"
    )

    print(
        "=" * 80
    )


    if not results:

        print(
            "No matching emails found."
        )

        print(
            "=" * 80
        )

        return


    print(
        f"Matches found : {len(results)}"
    )


    for index, item in enumerate(
        results,
        start=1
    ):

        print()

        print(
            "-" * 80
        )


        print(
            f"Result {index}"
        )


        print(
            f"Sender       : "
            f"{item.get('sender', '')}"
        )


        print(
            f"Subject      : "
            f"{item.get('subject', '')}"
        )


        print(
            f"Final Result : "
            f"{item.get('final_prediction', '')}"
        )


        print(
            f"Gmail Action : "
            f"{item.get('gmail_action', '')}"
        )


    print()

    print(
        "=" * 80
    )


# ------------------------------------------------------------
# CLEAR HISTORY
# ------------------------------------------------------------

def clear_history():

    history = load_history()


    if not history:

        print()

        print(
            "No history to clear."
        )

        return


    print()

    confirmation = input(
        "Are you sure you want to clear all history? (yes/no): "
    ).strip().lower()


    if confirmation == "yes":

        save_history([])

        print(
            "Email history cleared successfully."
        )

    else:

        print(
            "Clear operation cancelled."
        )


# ------------------------------------------------------------
# MENU
# ------------------------------------------------------------

def main():

    while True:

        print()

        print(
            "=" * 70
        )

        print(
            "              SMART EMAIL SYSTEM"
        )

        print(
            "                 EMAIL HISTORY"
        )

        print(
            "=" * 70
        )

        print()

        print(
            "1. View Email History"
        )

        print(
            "2. View History Summary"
        )

        print(
            "3. Search History"
        )

        print(
            "4. Clear History"
        )

        print(
            "5. Exit"
        )

        print()


        choice = input(
            "Enter your choice: "
        ).strip()


        if choice == "1":

            display_history()

            input(
                "\nPress Enter to continue..."
            )


        elif choice == "2":

            history_summary()

            input(
                "\nPress Enter to continue..."
            )


        elif choice == "3":

            search_history()

            input(
                "\nPress Enter to continue..."
            )


        elif choice == "4":

            clear_history()

            input(
                "\nPress Enter to continue..."
            )


        elif choice == "5":

            print()

            print(
                "Exiting Email History..."
            )

            break


        else:

            print()

            print(
                "Invalid choice."
            )


# ------------------------------------------------------------
# PROGRAM START
# ------------------------------------------------------------

if __name__ == "__main__":

    main()