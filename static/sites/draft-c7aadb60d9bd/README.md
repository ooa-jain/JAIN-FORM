# INTERN STAR — Setup (3 Steps)

## Step 1 — Get service_account.json

1. Go to https://console.cloud.google.com
2. Create a project → Enable "Google Sheets API"
3. IAM & Admin → Service Accounts → Create Service Account → name it anything
4. Click the service account → Keys → Add Key → JSON → Download
5. Rename the file to: service_account.json
6. Put it in the intern_star/ folder (same level as app.py)

## Step 2 — Share your Google Sheet

Open service_account.json, find "client_email", copy it.
Go to your Google Sheet → Share → paste that email → Editor → Share.

Your Sheet ID is already set in app.py:
174r5tkDujhmiFHjXwI7uRuu9Z57nc8bpeE5aWQ9ISOk

## Step 3 — Run

pip install -r requirements.txt
python app.py

Open http://localhost:5000
Fill the form → hit MISSION COMPLETE → data appears in sheet instantly.
