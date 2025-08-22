# api/index.py
import os
from flask import Flask, request, jsonify, send_from_directory, make_response
from supabase import create_client
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = Flask(__name__, static_folder="../static", static_url_path="/")

# -----------------------
def now_str():
    return datetime.utcnow().strftime("%m/%d/%y Time: %H:%M")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    return send_from_directory(app.static_folder, "index.html")

# -----------------------
# LOGIN (with Supabase Auth)
@app.route("/api/login", methods=["POST"])
def login():
    payload = request.json or {}
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    # Use supabase.auth.sign_in_with_password
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if not res or not getattr(res, "session", None):
        return jsonify({"error": "Invalid credentials"}), 401

    token = res.session.access_token
    user = res.user

    # Set token in HTTP-only cookie
    resp = make_response(jsonify({"ok": True, "user": {"id": user.id, "email": user.email}}))
    resp.set_cookie("sb_token", token, httponly=True, secure=True, samesite="Strict")
    return resp

# -----------------------
# LOGOUT
@app.route("/api/logout", methods=["POST"])
def logout():
    token = request.cookies.get("sb_token")
    if token:
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
    resp = make_response(jsonify({"ok": True, "message": "Logged out"}))
    resp.delete_cookie("sb_token")
    return resp

# -----------------------
# DASHBOARD endpoint (requires auth)
@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    token = request.cookies.get("sb_token")
    if not token:
        return jsonify({"error": "Not logged in"}), 401

    # Validate token
    try:
        user = supabase.auth.get_user(token)
    except Exception:
        return jsonify({"error": "Invalid or expired session"}), 401

    # Example: fetch balance + logs from custom tables
    uid = user.user.id
    user_row = supabase.table("users").select("*").eq("id", uid).limit(1).execute().data
    logs = supabase.table("logs").select("*").eq("user_id", uid).order("created_at", desc=True).limit(20).execute().data

    return jsonify({
        "user": user_row[0] if user_row else {"id": uid, "balance": 0},
        "logs": logs or []
    })

if __name__ == "__main__":
    app.run(debug=True)
