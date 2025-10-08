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
                    "block_id": "height",
                    "label": {"type": "plain_text", "text": "Height (cm)"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "height_input",
                    },
                },
                {
                    "type": "input",
                    "block_id": "weight",
                    "label": {"type": "plain_text", "text": "Weight (kg)"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "weight_input",
                    },
                },
            ],
        },
    }

    # Open the modal in Slack
    requests.post(
        "https://slack.com/api/views.open",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json=modal,
    )

    # Respond quickly (Slack requires <3s)
    return "", 200


# -------------------------------------------------------------------
# 2️⃣ Modal submission → trigger Jenkins job
# -------------------------------------------------------------------
@app.route("/slack/interactions", methods=["POST"])
def handle_interaction():
    payload = json.loads(request.form["payload"])

    if payload.get("type") == "view_submission":
        values = payload["view"]["state"]["values"]
        height = values["height"]["height_input"]["value"]
        weight = values["weight"]["weight_input"]["value"]
        user = payload["user"]["id"]

        # Trigger Jenkins job
        response = requests.post(
            JENKINS_URL,
            auth=(JENKINS_USER, JENKINS_TOKEN),
            params={"HEIGHT": height, "WEIGHT": weight, "USER": user},
        )

        if response.status_code == 201:
            print(f"Triggered Jenkins job for user {user}")
        else:
            print(f"Failed to trigger Jenkins job: {response.status_code} - {response.text}")

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
