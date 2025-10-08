from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

SLACK_BOT_TOKEN = "SLACKBOT_TOKEN"
JENKINS_URL = "JENKINS_URL"
JENKINS_USER = "JENKINS_USER"
JENKINS_TOKEN = "JENKINS_TOKEN"

# 1️⃣ Slash command trigger
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
                    "element": {"type": "plain_text_input", "action_id": "height_input"},
                },
                {
                    "type": "input",
                    "block_id": "weight",
                    "label": {"type": "plain_text", "text": "Weight (kg)"},
                    "element": {"type": "plain_text_input", "action_id": "weight_input"},
                },
            ],
        },
    }
    requests.post(
        "https://slack.com/api/views.open",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json=modal,
    )
    return "", 200

# 2️⃣ Modal submission
@app.route("/slack/interactions", methods=["POST"])
def handle_submission():
    payload = json.loads(request.form["payload"])
    if payload["type"] == "view_submission":
        values = payload["view"]["state"]["values"]
        height = values["height"]["height_input"]["value"]
        weight = values["weight"]["weight_input"]["value"]
        user = payload["user"]["id"]

        # Trigger Jenkins job
        res = requests.post(
            JENKINS_URL,
            auth=(JENKINS_USER, JENKINS_TOKEN),
            params={"HEIGHT": height, "WEIGHT": weight, "USER": user},
        )

        # Respond with ephemeral confirmation
        return jsonify({"response_action": "clear"}), 200

    return "", 200

# 3️⃣ Optional endpoint for Jenkins to report result
@app.route("/jenkins/result", methods=["POST"])
def receive_result():
    data = request.json
    user_id = data["user"]
    bmi = data["bmi"]
    thread_ts = data.get("thread_ts")

    msg = f"Your BMI is *{bmi}*"
    requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json={"channel": user_id, "text": msg, "thread_ts": thread_ts},
    )
    return "", 200


if __name__ == "__main__":
    app.run(port=5000)
