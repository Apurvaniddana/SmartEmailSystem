import re


# ============================================================
# SMART EMAIL SYSTEM
# SUBSCRIPTION DETECTOR
# ============================================================


# ------------------------------------------------------------
# NEWSLETTER / SUBSCRIPTION KEYWORDS
# ------------------------------------------------------------

SUBSCRIPTION_KEYWORDS = [

    "unsubscribe",
    "manage preferences",
    "email preferences",
    "subscription preferences",
    "mailing list",
    "newsletter",
    "weekly digest",
    "daily digest",
    "monthly digest",
    "you are receiving this email",
    "you received this email",
    "opt out",
    "opt-out",
    "stop receiving",
    "update preferences",
]


# ------------------------------------------------------------
# PROMOTIONAL KEYWORDS
# ------------------------------------------------------------

PROMOTIONAL_KEYWORDS = [

    "offer",
    "discount",
    "sale",
    "deal",
    "coupon",
    "promotion",
    "limited time",
    "special offer",
    "free",
    "bonus",
]


# ------------------------------------------------------------
# FIND UNSUBSCRIBE LINK
# ------------------------------------------------------------

def find_unsubscribe_link(message):

    if not message:
        return None

    patterns = [

        # HTML link where visible text contains unsubscribe
        r'href=["\']([^"\']+)["\'][^>]*>\s*[^<]*unsubscribe',

        # HTML href itself contains unsubscribe
        r'href=["\']([^"\']*unsubscribe[^"\']*)["\']',

        # Plain URL containing unsubscribe
        r'(https?://[^\s<>"\']*unsubscribe[^\s<>"\']*)',

        # Plain URL containing preferences
        r'(https?://[^\s<>"\']*preferences[^\s<>"\']*)',
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            message,
            re.IGNORECASE
        )

        if match:

            return match.group(1)

    return None


# ------------------------------------------------------------
# DETECT SUBSCRIPTION
# ------------------------------------------------------------

def detect_subscription(
    subject,
    message,
    sender
):

    subject = subject or ""
    message = message or ""
    sender = sender or ""

    combined_text = (
        subject
        + " "
        + message
        + " "
        + sender
    ).lower()

    indicators = []

    # --------------------------------------------------------
    # CHECK SUBSCRIPTION KEYWORDS
    # --------------------------------------------------------

    for keyword in SUBSCRIPTION_KEYWORDS:

        if keyword.lower() in combined_text:

            if keyword not in indicators:

                indicators.append(keyword)

    # --------------------------------------------------------
    # FIND UNSUBSCRIBE LINK
    # --------------------------------------------------------

    unsubscribe_link = find_unsubscribe_link(
        message
    )

    if unsubscribe_link:

        if "unsubscribe_link" not in indicators:

            indicators.append(
                "unsubscribe_link"
            )

    # --------------------------------------------------------
    # SUBSCRIPTION DETECTED
    # --------------------------------------------------------

    if indicators:

        return {

            "is_subscription": True,

            "type":
                "NEWSLETTER / SUBSCRIPTION",

            "indicators":
                indicators,

            "unsubscribe_available":
                unsubscribe_link is not None,

            "unsubscribe_link":
                unsubscribe_link
        }

    # --------------------------------------------------------
    # NORMAL EMAIL
    # --------------------------------------------------------

    return {

        "is_subscription": False,

        "type":
            "NORMAL EMAIL",

        "indicators":
            [],

        "unsubscribe_available":
            False,

        "unsubscribe_link":
            None
    }


# ------------------------------------------------------------
# DETECT PROMOTIONAL EMAIL
# ------------------------------------------------------------

def detect_promotional(
    subject,
    message
):

    subject = subject or ""
    message = message or ""

    combined_text = (
        subject
        + " "
        + message
    ).lower()

    indicators = []

    for keyword in PROMOTIONAL_KEYWORDS:

        if keyword.lower() in combined_text:

            if keyword not in indicators:

                indicators.append(keyword)

    if indicators:

        return {

            "is_promotional":
                True,

            "indicators":
                indicators
        }

    return {

        "is_promotional":
            False,

        "indicators":
            []
    }


# ------------------------------------------------------------
# DISPLAY RESULT
# ------------------------------------------------------------

def display_subscription_result(
    subject,
    sender,
    subscription_result,
    promotional_result
):

    print()

    print("=" * 60)

    print("SUBSCRIPTION ANALYSIS")

    print("=" * 60)

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

        if indicators:

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

    print("=" * 60)


# ------------------------------------------------------------
# TEST PROGRAM
# ------------------------------------------------------------

def main():

    print("=" * 60)

    print("SMART EMAIL SYSTEM")

    print("SUBSCRIPTION DETECTOR")

    print("=" * 60)

    test_emails = [

        {
            "sender":
                "LeetCode <no-reply@leetcode.com>",

            "subject":
                "LeetCode Weekly Digest",

            "message":
                """
                LeetCode Weekly Digest

                Here are this week's updates.

                You are receiving this email because
                you subscribed to LeetCode.

                Unsubscribe:

                https://leetcode.com/unsubscribe
                """
        },

        {
            "sender":
                "LinkedIn <newsletters-noreply@linkedin.com>",

            "subject":
                "Agile 101: Beginners Guide",

            "message":
                """
                Free Courses With Certificates

                Agile 101: Beginners Guide

                Manage your email preferences.

                Unsubscribe:

                https://www.linkedin.com/settings/email-preferences
                """
        },

        {
            "sender":
                "Google <noreply-accounts@google.com>",

            "subject":
                "You shared some Google Account data",

            "message":
                """
                You are receiving this security notification
                because you used Sign in with Google.

                This is an account security notification.
                """
        }
    ]

    for index, email in enumerate(
        test_emails,
        start=1
    ):

        print()

        print(
            f"Processing Test Email {index}"
        )

        subscription_result = detect_subscription(

            email["subject"],

            email["message"],

            email["sender"]
        )

        promotional_result = detect_promotional(

            email["subject"],

            email["message"]
        )

        display_subscription_result(

            email["subject"],

            email["sender"],

            subscription_result,

            promotional_result
        )


# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------

if __name__ == "__main__":

    main()