from flask import Flask, render_template, request, jsonify
from pagerduty import RestApiV2Client
import configparser
import requests
import os
import http.client
import json
from urllib.parse import urlparse


print("Current working directory:", os.getcwd())
app = Flask(__name__)


def load_api_token():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config.get('PagerDuty', 'api_token')


def load_from_email():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config.get('PagerDuty', 'from_email')


@app.route('/')
def index():
    return render_template('updated_index.html')


@app.route('/fetch', methods=['POST'])
def fetch_incident():
    ticket_number = request.form['ticket_number']
    api_token = load_api_token()
    session = RestApiV2Client(api_token)
    incident = session.rget(f"/incidents/{ticket_number}")
    ppn = incident.get("priority", {}).get("name", "P1").replace("P", "")
    ptl = incident.get("title", "N/A")
    lnk = f"https://discoveryinc.pagerduty.com/incidents/{ticket_number}"
    title = f"SEV {ppn}\n {ptl}\n {lnk}"
    return jsonify({"title": title})


@app.route('/update', methods=['POST'])
def update_incident():
    ticket_number = request.form.get('ticket_number')
    note = request.form.get('note')
    print("Debug - Received ticket_number:", ticket_number)
    print("Debug - Received note:", note)

    if not ticket_number or not note:
        return jsonify({"status": "error", "message": "Missing ticket_number or note"}), 400

    api_token = load_api_token()
    from_email = load_from_email()

    headers = {
        'Accept': "application/json",
        'Content-Type': "application/json",
        'From': from_email,
        'Authorization': f"Token token={api_token}"
    }

    try:
        # Add note to incident
        note_url = f"https://api.pagerduty.com/incidents/{ticket_number}/notes"
        parsed_note_url = urlparse(note_url)
        note_payload = json.dumps({
            "note": {
                "content": note
            }
        })

        conn = http.client.HTTPSConnection(parsed_note_url.hostname)
        conn.request("POST", parsed_note_url.path, body=note_payload, headers=headers)
        note_response = conn.getresponse()
        note_data = note_response.read().decode("utf-8")
        print("Debug - Note response:", note_data)

        # Send status update with same message as note
        status_url = f"https://api.pagerduty.com/incidents/{ticket_number}/status_updates/"
        parsed_status_url = urlparse(status_url)

        status_payload = json.dumps({
            "status_update": {
             "message": note
           }
        })

        conn = http.client.HTTPSConnection(parsed_status_url.hostname)
        conn.request("POST", parsed_status_url.path, body=status_payload, headers=headers)
        status_response = conn.getresponse()
        status_data = status_response.read().decode("utf-8")
        print("Debug - Status update response code:", status_response.status)
        print("Debug - Status update response body:", status_data)

        return jsonify({"status": "success", "message": "Note added and status update sent."})

    except Exception as e:
        print("Debug - Exception occurred:", str(e))
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5001)
