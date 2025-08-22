from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client

app = Flask(__name__, template_folder="templates")

# --- Supabase Setup ---
SUPABASE_URL = "https://hzjqmssccnxddsbqliaq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh6anFtc3NjY254ZGRzYnFsaWFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQxOTYzNjMsImV4cCI6MjA2OTc3MjM2M30.pzdW7pPHjCPqO9VJLF_kYoXcRVONO1YP2RVHkRyzOEk"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/fetch_or_create", methods=["POST"])
def fetch_or_create():
    data = request.json
    name = data.get("name")
    acc_id = data.get("id")

    # Try fetch
    res = supabase.table("accounts").select("*").eq("id", acc_id).execute()
    if res.data:
        return jsonify(res.data[0])

    # Create if not exists
    new_acc = {"id": acc_id, "name": name, "balance": 0}
    res = supabase.table("accounts").insert(new_acc).execute()
    return jsonify(res.data[0])

@app.route("/update_balance", methods=["POST"])
def update_balance():
    data = request.json
    acc_id = data.get("id")
    new_balance = data.get("balance")

    res = supabase.table("accounts").update({"balance": new_balance}).eq("id", acc_id).execute()
    return jsonify(res.data[0])
