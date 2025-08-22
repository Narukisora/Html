# api/index.py
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from supabase import create_client

# Get Supabase env variables from Vercel project settings
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not (SUPABASE_URL and SUPABASE_KEY):
    raise Exception("Set SUPABASE_URL and SUPABASE_KEY in environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__, static_folder="../static", static_url_path="/")

# -----------------------
# Helper: format timestamp
def now_str():
    return datetime.utcnow().strftime("%m/%d/%y Time: %H:%M")

# -----------------------
# Serve frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    # serve static index.html for all routes (SPA)
    return send_from_directory(app.static_folder, "index.html")

# -----------------------
# Login endpoint
@app.route("/api/login", methods=["POST"])
def login():
    payload = request.json or {}
    name = payload.get("name", "").strip()
    uid = payload.get("id", "").strip()
    if not name or not uid:
        return jsonify({"error": "name and id required"}), 400

    # look up user (table: users) by id and name
    resp = supabase.table("users").select("*").eq("id", uid).eq("name", name).limit(1).execute()
    data = resp.data
    if not data:
        return jsonify({"found": False}), 200

    user = data[0]
    # fetch logs (logs table) latest first
    logs_resp = supabase.table("logs").select("*").eq("user_id", uid).order("created_at", desc=True).limit(20).execute()
    logs = logs_resp.data or []

    return jsonify({
        "found": True,
        "user": {
            "id": user.get("id"),
            "name": user.get("name"),
            "balance": user.get("balance", 0)
        },
        "logs": logs
    })

# -----------------------
# Change balance (set to value)
@app.route("/api/change", methods=["POST"])
def change_balance():
    payload = request.json or {}
    uid = payload.get("id")
    new_balance = payload.get("balance")
    reason = payload.get("reason", "Change")
    if uid is None or new_balance is None:
        return jsonify({"error": "id and balance required"}), 400

    # update users table
    update_resp = supabase.table("users").update({"balance": new_balance}).eq("id", uid).execute()

    # insert log entry
    log_entry = {
        "user_id": uid,
        "amount": new_balance - (payload.get("prev_balance") or 0),  # optional
        "notes": f"{reason} (set to {new_balance})",
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("logs").insert(log_entry).execute()

    return jsonify({"ok": True, "balance": new_balance})

# -----------------------
# Deduct amount (subtract)
@app.route("/api/deduct", methods=["POST"])
def deduct():
    payload = request.json or {}
    uid = payload.get("id")
    amount = payload.get("amount")
    if uid is None or amount is None:
        return jsonify({"error": "id and amount required"}), 400

    # Fetch current balance
    user_resp = supabase.table("users").select("balance").eq("id", uid).limit(1).execute()
    users = user_resp.data
    if not users:
        return jsonify({"error": "user not found"}), 404

    prev_balance = users[0].get("balance", 0)
    new_balance = prev_balance - amount

    # Update user balance
    supabase.table("users").update({"balance": new_balance}).eq("id", uid).execute()

    # Insert log
    log_entry = {
        "user_id": uid,
        "amount": -abs(amount),
        "notes": f"Deduct {amount}₱",
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("logs").insert(log_entry).execute()

    # Return new balance and a formatted log line
    log_line = f"-{amount}₱\n{datetime.utcnow().strftime('%m/%d/%y Time: %H:%M')}"
    return jsonify({
        "ok": True,
        "balance": new_balance,
        "log_line": log_line,
        "prev_balance": prev_balance
    })

# -----------------------
if __name__ == "__main__":
    app.run(debug=True)
