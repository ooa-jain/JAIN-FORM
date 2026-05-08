from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from datetime import datetime
from bson import ObjectId
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("JWT_SECRET", "memberprofile_secret")
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# ── PUBLIC ────────────────────────────────────────────

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
        mongo.db.members.insert_one(data)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── ADMIN ─────────────────────────────────────────────

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASS:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Invalid credentials"
    return render_template("admin_login.html", error=error)

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    members = list(mongo.db.members.find().sort("submitted_at", -1))
    for m in members:
        m["_id"] = str(m["_id"])
    return render_template("admin_dashboard.html", members=members, count=len(members))

@app.route("/admin/delete/<id>", methods=["POST"])
def admin_delete(id):
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 401
    mongo.db.members.delete_one({"_id": ObjectId(id)})
    return jsonify({"success": True})

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
