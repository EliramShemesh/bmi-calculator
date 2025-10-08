import os
import json
import threading
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# -------------------------------------------------------------------
#  Setup
# -------------------------------------------------------------------
load_dotenv()
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# 🔐 Secrets from environment
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

logging.debug(">>> SLACK_BOT_TOKEN in Flask:", SLACK_BOT_TOKEN[:12] if SLACK_BOT_TOKEN else "None")

# -------------------------------------------------------------------
# 1️⃣ Slash command (/bmi) → open modal in Slack
# -------------------------------------------------------------------
@app.route("/bmi", methods=["POST"])
def open_modal():
    logging.debug("Received /bmi command")
    logging.debug("Form data: %s", request.form)

    trigger_id = request.form.get("trigger_id")
    if not trigger_id:
        logging.error("No trigger_id found in the request!")
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

    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}", "Content-Type": "application/json; charset=utf-8"}
    response = requests.post("https://slack.com/api/views.open", headers=headers, json=modal)
    logging.debug("Slack views.open response: %s", response.text)

    return "", 200

# -------------------------------------------------------------------
# 2️⃣ Modal submission → trigger Jenkins job
# -------------------------------------------------------------------
@app.route("/slack/interactions", methods=["POST"])
def handle_interactions():
    logging.debug("Received Slack interaction")
    logging.debug("Form data: %s", request.form)
    logging.debug("Raw data: %s", request.get_data())

    payload_str = request.form.get("payload")
    if not payload_str:
        logging.error("No payload found!")
        return "No payload found", 400

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logging.error("Invalid JSON payload: %s", payload_str)
        return "Invalid JSON payload", 400

    logging.debug("Parsed payload: %s", json.dumps(payload, indent=2))

    if payload.get("type") == "view_submission":
        values = payload["view"]["state"]["values"]
        try:
            height = values["height_block"]["height_input"]["value"]
            weight = values["weight_block"]["weight_input"]["value"]
            user_id = payload["user"]["id"]
        except KeyError as e:
            logging.error("KeyError accessing values: %s\nValues: %s", e, json.dumps(values, indent=2))
            return "Bad payload structure", 400

        logging.info("User %s submitted height=%s, weight=%s", user_id, height, weight)

        # Trigger Jenkins asynchronously
        def trigger_jenkins():
            try:
                response = requests.post(
                    f"{JENKINS_URL}/job/BMI-Calculator/buildWithParameters",
                    auth=(JENKINS_USER, JENKINS_TOKEN),
                    params={"HEIGHT": height, "WEIGHT": weight, "USER": user_id},
                )
                logging.info("Jenkins response: %s %s", response.status_code, response.text)
            except Exception as e:
                logging.error("Error triggering Jenkins: %s", e)

        threading.Thread(target=trigger_jenkins).start()
        logging.debug("Jenkins trigger thread started")

        return jsonify({"response_action": "clear"})

    logging.debug("Interaction type not handled: %s", payload.get("type"))
    return "", 200

# -------------------------------------------------------------------
# 3️⃣ Jenkins callback → post result back to Slack
# -------------------------------------------------------------------
@app.route("/jenkins/result", methods=["POST"])
def receive_result():
    data = request.json
    logging.debug("Received Jenkins result: %s", data)

    user_id = data.get("user")
    bmi = data.get("bmi")

    if not user_id or not bmi:
        logging.error("Invalid data from Jenkins: %s", data)
        return "Invalid data", 400

    message = f"Your BMI is *{bmi}*"

    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json={"channel": user_id, "text": message},
    )
    logging.debug("Slack chat.postMessage response: %s", response.text)

    return "", 200

# -------------------------------------------------------------------
# 4️⃣ Health check
# -------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def home():
    logging.debug("Health check requested")
    return "Slack ↔ Jenkins BMI integration is running!", 200

# -------------------------------------------------------------------
#  Run the Flask server
# -------------------------------------------------------------------
if __name__ == "__main__":
    logging.info("Starting Flask server on 0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080, debug=True)
