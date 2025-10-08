#!/usr/bin/env python3
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import requests
import json

# Load environment variables from .env file (for local dev)
load_dotenv()

app = Flask(__name__)

# 🔐 Secrets from environment (never hardcode these)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

# -------------------------------------------------------------------
# 1️⃣ Slash command (/bmi) → open modal in Slack
# -------------------------------------------------------------------
@app.route("/bmi", methods=["POST"])
def open_modal():
    trigger_id = request.form.get("trigger_id")
    if not trigger_id:
        return "No trigger_id found", 400

    modal = {
        "trigger_id": trigger_id,
        "view": {
            "type": "modal",
            "callback_id": "bmi_form",
            "title": {"type": "plain_text", "text": "BMI Calculator"},
            "submit": {"type": "plain_text", "text": "Calculate"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "height_block",
                    "label": {"type": "plain_text", "text": "Height (cm)"},
                    "element": {"type": "plain_text_input", "action_id": "height_input"},
                },
                {
                    "type": "input",
                    "block_id": "weight_block",
                    "label": {"type": "plain_text", "text": "Weight (kg)"},
                    "element": {"type": "plain_text_input", "action_id": "weight_input"},
                },
            ],
        },
    }

    # Call Slack API to open modal
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    r = requests.post("https://slack.com/api/views.open", headers=headers, json=modal)
    print(r.text)  # Always log Slack response for debugging

    return "", 200


# -------------------------------------------------------------------
# 2️⃣ Modal submission → trigger Jenkins job
# -------------------------------------------------------------------
@app.route("/slack/interactions", methods=["POST"])
def handle_interaction():
    payload_str = request.form.get("payload")
    if not payload_str:
        return "No payload found", 400

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        return "Invalid JSON payload", 400

    # Only handle modal submissions
    if payload.get("type") == "view_submission" and payload.get("view"):
        values = payload["view"]["state"]["values"]

        # ✅ Use the correct block IDs from your modal
        height = values["height"]["height_input"]["value"]
        weight = values["weight"]["weight_input"]["value"]
        user_id = payload["user"]["id"]

        # Trigger Jenkins job asynchronously
        import threading
        def trigger_jenkins():
            try:
                response = requests.post(
                    f"{JENKINS_URL}/job/bmi_job/buildWithParameters",
                    auth=(JENKINS_USER, JENKINS_TOKEN),
                    params={"HEIGHT": height, "WEIGHT": weight, "USER": user_id},
                )
                if response.status_code == 201:
                    print(f"Triggered Jenkins job for user {user_id}")
                else:
                    print(f"Failed to trigger Jenkins job: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error triggering Jenkins: {e}")

        threading.Thread(target=trigger_jenkins).start()

        # Close modal immediately
        return jsonify({"response_action": "clear"})

    return "", 200

# -------------------------------------------------------------------
# 3️⃣ Jenkins callback → post result back to Slack
# -------------------------------------------------------------------
@app.route("/jenkins/result", methods=["POST"])
def receive_result():
    data = request.json
    user_id = data["user"]
    bmi = data["bmi"]

    message = f"Your BMI is *{bmi}*"

    requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json={"channel": user_id, "text": message},
    )

    return "", 200


# -------------------------------------------------------------------
# 4️⃣ Health check
# -------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return "Slack ↔ Jenkins BMI integration is running!", 200


# -------------------------------------------------------------------
#  Run the Flask server
# -------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
