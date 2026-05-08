from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from datetime import datetime
from bson import ObjectId
import os
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("JWT_SECRET", "internstar_secret")
app.config["MONGO_URI"] = os.getenv("MONGO_URI")

mongo = PyMongo(app)

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# ── PUBLIC ROUTES ─────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "No data received"}), 400
    try:
        data["submitted_at"] = datetime.utcnow().isoformat()
        mongo.db.submissions.insert_one(data)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── ADMIN ROUTES ──────────────────────────────────────

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u == ADMIN_USER and p == ADMIN_PASS:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Invalid credentials"
    return render_template("admin_login.html", error=error)

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    submissions = list(mongo.db.submissions.find().sort("submitted_at", -1))
    for s in submissions:
        s["_id"] = str(s["_id"])
    return render_template("admin_dashboard.html", submissions=submissions, count=len(submissions))

@app.route("/admin/api/submissions")
def admin_api():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 401
    submissions = list(mongo.db.submissions.find().sort("submitted_at", -1))
    for s in submissions:
        s["_id"] = str(s["_id"])
    return jsonify(submissions)

@app.route("/admin/delete/<id>", methods=["POST"])
def admin_delete(id):
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 401
    mongo.db.submissions.delete_one({"_id": ObjectId(id)})
    return jsonify({"success": True})

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
