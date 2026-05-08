from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from datetime import datetime, timezone
import os
from functools import wraps
from bson import ObjectId
import json
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "formcraft-secret-jain-2024-xK9mP2qRuse")

# ── MongoDB ──────────────────────────────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is not set!")

client = MongoClient(MONGO_URI)
db = client["mango"]
responses_col = db["responses"]

# ── Admin credentials ────────────────────────────────────────────────────────
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")   # username is fine as default
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD environment variable is not set!")

# ── Auth decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

# ── Helper: serialize ObjectId ────────────────────────────────────────────────
def serialize(doc):
    doc["_id"] = str(doc["_id"])
    return doc

# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the influencer collaboration form."""
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    """Receive JSON form data and store in MongoDB."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False, "error": "No data received"}), 400

    # Attach server-side timestamp
    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    data["_date"] = datetime.now(timezone.utc).strftime("%a %b %d %Y")  # match JS toDateString()

    result = responses_col.insert_one(data)
    return jsonify({"ok": True, "id": str(result.inserted_id)}), 201


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Invalid username or password."
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    """Admin dashboard — serves the admin SPA."""
    return render_template("admin.html")


@app.route("/admin/api/responses")
@login_required
def api_responses():
    """Return all responses as JSON for the admin table."""
    docs = [serialize(d) for d in responses_col.find().sort("timestamp", -1)]
    return jsonify(docs)


@app.route("/admin/api/stats")
@login_required
def api_stats():
    today = datetime.now(timezone.utc).strftime("%a %b %d %Y")
    total       = responses_col.count_documents({})
    bangalore   = responses_col.count_documents({"location": "Bangalore"})
    kochi       = responses_col.count_documents({"location": "Kochi"})
    today_count = responses_col.count_documents({"_date": today})
    return jsonify({
        "total": total,
        "bangalore": bangalore,
        "kochi": kochi,
        "today": today_count
    })


@app.route("/admin/api/delete/<doc_id>", methods=["DELETE"])
@login_required
def api_delete(doc_id):
    responses_col.delete_one({"_id": ObjectId(doc_id)})
    return jsonify({"ok": True})


@app.route("/admin/api/clear", methods=["DELETE"])
@login_required
def api_clear():
    result = responses_col.delete_many({})
    return jsonify({"ok": True, "deleted": result.deleted_count})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
