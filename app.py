from flask import Flask, render_template, request, jsonify
from pagerduty import RestApiV2Client
import configparser

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

    if not ticket_number or not note:
        return jsonify({"status": "error", "message": "Missing ticket_number or note"}), 400

    api_token = load_api_token()
    session = RestApiV2Client(api_token)

    try:
        session.rpost(f"/incidents/{ticket_number}/notes", data={
            "note": {
                "content": note
            }
        })
        return jsonify({"status": "success", "message": "Note added to incident."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
