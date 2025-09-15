from flask import Flask, render_template, request, jsonify
from pagerduty import RestApiV2Client
import configparser
import os

print("Current working directory:", os.getcwd())

app = Flask(__name__)

def load_api_token():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config.get('PagerDuty', 'api_token')

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
    title = f"SEV {ppn} | {ptl} | {lnk}"

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
    session = RestApiV2Client(api_token)
    try:
        data = {
            "content": note
        }
        print("Debug - Data sent to PagerDuty:", data)
        response = session.rpost(f"/incidents/{ticket_number}/notes", data=data)
        print("Debug - PagerDuty response:", response)
        # Check if the response indicates success
        if response.get("error"):
            return jsonify({"status": "error", "message": response["error"]})
        # Send a status update using the "Default" template
        session.rpost(f"/incidents/{ticket_number}/status_updates", data={
            "message_template": "Default"
        })
        return jsonify({"status": "success", "message": "Note added and status update sent."})
    except Exception as e:
        print("Debug - Exception occurred:", str(e))
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True,port=5001)
