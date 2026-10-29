# Smart Email System

**Machine Learning-Based Secondary Spam Email Detection Using Data Balancing Techniques**

Smart Email System is a Python application built with Streamlit that helps users review and classify emails, identify potential spam and phishing risks, and manage subscriptions. It integrates a TF-IDF text representation and a Linear Support Vector Classifier (Linear SVC) with Gmail access through Google OAuth 2.0 and the Gmail API.

## Features

- **Email classification:** classify email content as SPAM, HAM, or UNCERTAIN using the saved machine-learning model.
- **Gmail integration:** connect a Google account through OAuth 2.0 and access supported Gmail functions.
- **Security review:** surface potential phishing indicators and suspicious links/content.
- **Email history:** keep classification/history records in JSON files.
- **Subscription management:** identify and manage subscription-related senders.
- **Email cleanup:** review unwanted senders/messages and use the available cleanup controls.
- **Multi-account support:** keep user-specific data and OAuth tokens separated when using the multi-account dashboard.
- **Streamlit dashboard:** use the app through a browser-based interface.

> Exact features depend on the `dashboard.py` version included in your repository. The README should be updated if you replace that file with a different version.

## Technology Stack

- Python
- Streamlit
- scikit-learn — Linear SVC model
- TF-IDF vectorizer
- pandas — data handling where required
- Google OAuth 2.0
- Gmail API
- JSON files for local application data

## Project Structure

The main project files are expected to be organized approximately like this:

```text
SmartEmailSystem/
├── dashboard.py
├── google_oauth_client.json       # Local only; do not commit
├── requirements.txt
├── README.md
├── email_system/
│   ├── gmail_classifier.py
│   ├── subscription_manager.py
│   ├── subscription_detector.py
│   └── email_history.py
├── saved_model/
│   ├── improved_linear_svc.pkl
│   └── improved_tfidf_vectorizer.pkl
├── dataset/
│   └── enron_spam_data.csv        # If included in your repository
└── data/
    ├── email_history.json         # Local/private data; do not commit
    ├── subscriptions.json         # Local/private data; do not commit
    ├── google_tokens/             # Local only; do not commit
    └── users/                     # Local user data; do not commit
```

Some folders and files are created automatically when the application runs. Your repository may not contain every example shown above.

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer recommended
- A modern web browser
- Google account for Gmail features
- Google Cloud project with the Gmail API enabled and OAuth credentials configured

## Installation on Windows

Open PowerShell in the project folder.

### 1. Create and activate a virtual environment

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the environment's Python executable directly in later commands instead.

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Check required model files

Confirm these files exist:

```text
saved_model/improved_linear_svc.pkl
saved_model/improved_tfidf_vectorizer.pkl
```

The app may not be able to classify emails if the trained model or vectorizer files are missing. Use the model files supplied with the project; do not replace them with unrelated pickle files.

### 4. Configure Google OAuth 2.0

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Select or create a Google Cloud project.
3. Enable **Gmail API** under **APIs & Services → Library**.
4. Configure the Google Auth Platform / OAuth consent screen.
5. If the app is in Testing mode, add the Google account you will use as a test user.
6. Create an OAuth client ID. For the current local setup, configure the redirect URI as:

   ```text
   http://localhost:8501
   ```

7. Download the OAuth client JSON and save it in the project root as:

   ```text
   google_oauth_client.json
   ```

**Never commit OAuth client files, client secrets, access tokens, or refresh tokens to GitHub.** Keep them local and make sure they are excluded by `.gitignore`. The redirect URI must match the one configured in Google Cloud Console. For deployment, configure the exact deployed redirect URI and set `GOOGLE_REDIRECT_URI` accordingly.

### 5. Run the application

```powershell
python -m streamlit run dashboard.py
```

Streamlit normally opens the app in your browser at `http://localhost:8501`.

## Data and privacy

The app may store classification history, subscription information, per-user data, and Google OAuth tokens in local files under `data/`. These files can contain private information. Do not upload real email history, subscription records, tokens, or other personal data to a public repository.

If your version of the project uses multi-account support, verify that `data/google_tokens/` and `data/users/` remain private and excluded from version control.

## Troubleshooting

- **`ModuleNotFoundError`:** activate the virtual environment and run `pip install -r requirements.txt`.
- **Model/vectorizer file not found:** verify the two `.pkl` files are present in `saved_model/`.
- **OAuth `invalid_client`:** verify the local OAuth JSON file and client configuration.
- **OAuth `redirect_uri_mismatch`:** make sure the redirect URI in Google Cloud Console exactly matches the URI used by the app.
- **`access_denied` while in Testing mode:** add the Google account as a test user on the OAuth consent screen.
- **Gmail API quota errors:** wait before retrying and avoid repeated requests in quick succession.
- **Permission or token errors:** revoke invalid credentials and complete the Google sign-in flow again.

## Security notes

- Do not publish OAuth secrets, access tokens, refresh tokens, `.env` files, or private JSON data.
- If credentials were accidentally pushed to a remote repository, remove them from the repository history **and revoke/rotate the exposed credentials**. Deleting a file in a later commit does not invalidate a token or secret.
- Review the Google OAuth scopes requested by the application and grant only the permissions needed for its functionality.

## GitHub

Repository: https://github.com/Apurvaniddana/SmartEmailSystem

## Academic Project

**Project title:** Smart Email System: Machine Learning-Based Secondary Spam Email Detection Using Data Balancing Techniques
