# Member Profile Form — Flask + MongoDB

## Setup

```bash
# 1. Create venv and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Create .env (already set with MongoDB URI)
# Edit .env if needed

# 3. Run
python app.py
```

## Deploy on Hostinger (port 8021)

```bash
# Nginx config server_name: your-domain.com
# proxy_pass http://127.0.0.1:8021

# Systemd service:
ExecStart=/var/www/member-profile/venv/bin/gunicorn --bind 127.0.0.1:8021 app:app

sudo systemctl daemon-reload
sudo systemctl enable member-profile
sudo systemctl start member-profile
```

## Admin
- URL: /admin
- Username: admin
- Password: admin123

## Features
- 5-step form with validation
- Saves to MongoDB (Draftspace DB, members collection)
- Admin dashboard: view, search, delete, export CSV/TXT per member
