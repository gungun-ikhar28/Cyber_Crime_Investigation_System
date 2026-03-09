from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, send_file
import hashlib
import os
import json
import socket
import requests
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for chat messages, case data, and complaints
chat_messages = []
case_evidence_log = []
complaints = []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        hash_input = request.form.get('hash')

        if uploaded_file and hash_input:
            file_content = uploaded_file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()

            if file_hash == hash_input:
                result = "Evidence Verified Successfully ✅"
            else:
                result = "Hash Mismatch! Evidence Verification Failed ❌"

            # Save file to uploads folder
            filename = uploaded_file.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            with open(filepath, 'wb') as f:
                f.write(file_content)

            # Log to chain of custody
            case_evidence_log.append({
                'filename': filename,
                'sha256': file_hash,
                'uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'verified': file_hash == hash_input,
                'action': 'Upload & Verify'
            })

            return render_template('result.html', result=result, actual_hash=file_hash)
        else:
            flash("Please select file and enter hash!", "error")
            return redirect(url_for('upload'))

    return render_template('upload.html')


@app.route('/evidence')
def evidence():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('evidence.html', files=files)


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file:
            file_content = uploaded_file.read()
            generated_hash = hashlib.sha256(file_content).hexdigest()
            result = "SHA256 Hash Generated Successfully ✅"
            return render_template('verify_result.html', result=result, generated_hash=generated_hash)
        else:
            flash("Please select a file!", "error")
            return redirect(url_for('verify'))
    return render_template('verify.html')


# =================== FILE COMPLAINT ===================
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        crime_type = request.form.get('crime_type', '').strip()
        description = request.form.get('description', '').strip()
        suspect_info = request.form.get('suspect_info', '').strip()

        if not name or not crime_type or not description:
            flash('Name, Crime Type, and Description are required!', 'error')
            return redirect(url_for('complaint'))

        complaint_id = f'CYB-{datetime.now().strftime("%Y%m%d")}-{len(complaints) + 1:04d}'
        complaint_data = {
            'id': complaint_id,
            'name': name,
            'email': email,
            'phone': phone,
            'crime_type': crime_type,
            'description': description,
            'suspect_info': suspect_info,
            'status': 'Pending',
            'filed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        complaints.append(complaint_data)
        return render_template('complaint_success.html', complaint=complaint_data)

    return render_template('complaint.html')


@app.route('/complaints')
def view_complaints():
    return render_template('complaints_list.html', complaints=complaints)


# =================== IP TRACKING ===================
@app.route('/ip_tracking', methods=['GET', 'POST'])
def ip_tracking():
    ip_info = None
    error = None
    if request.method == 'POST':
        ip_address = request.form.get('ip_address', '').strip()
        if ip_address:
            try:
                # Use ip-api.com free API for IP geolocation
                resp = requests.get(
                    f'http://ip-api.com/json/{ip_address}',
                    params={'fields': 'status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query'},
                    timeout=10
                )
                data = resp.json()
                if data.get('status') == 'success':
                    ip_info = data
                else:
                    error = f"Lookup failed: {data.get('message', 'Invalid IP address')}"
            except requests.exceptions.RequestException:
                error = "Network error: Could not reach IP lookup service."
        else:
            error = "Please enter an IP address."
    return render_template('ip_tracking.html', ip_info=ip_info, error=error)


# =================== CHAT SYSTEM ===================
@app.route('/chat')
def chat():
    return render_template('chat.html')


@app.route('/chat/send', methods=['POST'])
def chat_send():
    data = request.get_json()
    username = data.get('username', 'Anonymous')
    message = data.get('message', '').strip()
    if message:
        chat_messages.append({
            'username': username,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify({'status': 'ok'})


@app.route('/chat/messages')
def chat_get_messages():
    return jsonify(chat_messages)


# =================== GENERATE REPORT (Chain of Custody) ===================
@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        case_number = request.form.get('case_number', 'N/A')
        investigator = request.form.get('investigator', 'N/A')
        department = request.form.get('department', 'N/A')
        description = request.form.get('description', 'N/A')

        # Gather evidence files info
        evidence_entries = []
        for entry in case_evidence_log:
            evidence_entries.append(entry)

        # Also add any files in uploads that aren't logged yet
        uploaded_files = os.listdir(UPLOAD_FOLDER)
        logged_filenames = {e['filename'] for e in case_evidence_log}
        for fname in uploaded_files:
            if fname not in logged_filenames:
                fpath = os.path.join(UPLOAD_FOLDER, fname)
                with open(fpath, 'rb') as f:
                    content = f.read()
                evidence_entries.append({
                    'filename': fname,
                    'sha256': hashlib.sha256(content).hexdigest(),
                    'uploaded_at': datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M:%S'),
                    'verified': False,
                    'action': 'Pre-existing'
                })

        report_data = {
            'case_number': case_number,
            'investigator': investigator,
            'department': department,
            'description': description,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'evidence_entries': evidence_entries
        }

        return render_template('report_view.html', report=report_data)

    return render_template('report.html')


if __name__ == '__main__':
    app.run(debug=True)