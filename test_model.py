import os
import pickle

# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
# CHECK MODEL FILES
# ============================================================

print("Checking model files...")

if not os.path.exists(MODEL_FILE):
    print("ERROR: Model file not found!")
    print(MODEL_FILE)
    exit()

print("Model file found.")


if not os.path.exists(VECTORIZER_FILE):
    print("ERROR: Vectorizer file not found!")
    print(VECTORIZER_FILE)
    exit()

print("Vectorizer file found.")


# ============================================================
# LOAD MODEL
# ============================================================

print()
print("Loading model...")

with open(MODEL_FILE, "rb") as f:
    model = pickle.load(f)

print("Model loaded.")


# ============================================================
# LOAD VECTORIZER
# ============================================================

print("Loading vectorizer...")

with open(VECTORIZER_FILE, "rb") as f:
    vectorizer = pickle.load(f)

print("Vectorizer loaded.")


# ============================================================
# FINAL DECISION
# ============================================================

def final_decision(ml_prediction, score):

    ml_prediction = str(ml_prediction).upper()

    # --------------------------------------------------------
    # SPAM
    # --------------------------------------------------------

    if ml_prediction == "SPAM":

        if score >= 0.10:
            confidence = "HIGH CONFIDENCE SPAM"

        else:
            confidence = "POSSIBLE SPAM"

        return "SPAM", confidence


    # --------------------------------------------------------
    # HAM
    # --------------------------------------------------------

    else:

        if score <= -0.10:
            confidence = "HIGH CONFIDENCE HAM"

        else:
            confidence = "POSSIBLE HAM"

        return "HAM", confidence


# ============================================================
# TEST EMAILS
# ============================================================

test_emails = [

    "Congratulations! You have won a free prize. Click here to claim your money now!",

    "URGENT! Your account has been suspended. Verify your password immediately.",

    "You have won $10000. Claim your prize now!",

    "Reminder: Call for Paper at NIT Rourkela.",

    "Your LinkedIn profile is getting hits.",

    "Welcome to Emertxe Internship 2026 – Kickoff Meeting Today",

    "New openings based on your profile!",

    "Introducing Napkin Slides",

    "Fast-track your career and win exciting prizes!",

    "YouTube live session about an internship."

]


# ============================================================
# PROCESS EMAILS
# ============================================================

print()
print("===================================")
print("SMART EMAIL ML TEST")
print("===================================")


spam_count = 0
ham_count = 0
errors = 0


for number, email_text in enumerate(test_emails, start=1):

    print()
    print("-----------------------------------")
    print(f"Test Email {number}")
    print("-----------------------------------")

    print()
    print(f"Text       : {email_text}")

    try:

        # ----------------------------------------------------
        # TF-IDF TRANSFORMATION
        # ----------------------------------------------------

        features = vectorizer.transform(
            [email_text]
        )


        # ----------------------------------------------------
        # ML PREDICTION
        # ----------------------------------------------------

        prediction = model.predict(
            features
        )[0]


        # ----------------------------------------------------
        # DECISION SCORE
        # ----------------------------------------------------

        score = model.decision_function(
            features
        )[0]


        # ----------------------------------------------------
        # FINAL DECISION
        # ----------------------------------------------------

        final_prediction, confidence = final_decision(
            prediction,
            score
        )


        # ----------------------------------------------------
        # COUNT
        # ----------------------------------------------------

        if final_prediction == "SPAM":
            spam_count += 1

        else:
            ham_count += 1


        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        print(
            f"ML Output  : {str(prediction).upper()}"
        )

        print(
            f"ML Score   : {score:.4f}"
        )

        print(
            f"FINAL      : {final_prediction}"
        )

        print(
            f"CONFIDENCE : {confidence}"
        )


    except Exception as error:

        errors += 1

        print()
        print("ERROR:")
        print(error)


# ============================================================
# SUMMARY
# ============================================================

print()
print("===================================")
print("CLASSIFICATION SUMMARY")
print("===================================")

print(
    f"HAM emails       : {ham_count}"
)

print(
    f"SPAM emails      : {spam_count}"
)

print(
    f"Errors           : {errors}"
)

print(
    f"Total processed  : {len(test_emails)}"
)

print("===================================")