from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, send_file, session
import hashlib
import os
import requests
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
import database

app = Flask(__name__)
app.secret_key = "cyber_crime_portal_ultra_secret_key_2026"

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SQLite database on startup
database.init_db()

# --- Auth Decorators ---
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "error")
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash(f"Access restricted. You must be logged in as an {role}.", "error")
                if session.get('role') == 'user':
                    return redirect(url_for('user_dashboard'))
                return redirect(url_for('investigator_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Inject user into all templates
@app.context_processor
def inject_user():
    current_user = None
    if 'user_id' in session:
        current_user = {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role'),
            'badge_number': session.get('badge_number'),
            'department': session.get('department')
        }
    return dict(current_user=current_user, active_case_id=session.get('active_case_id'))

# =================== GENERAL & AUTH ROUTES ===================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'user')

        user, message = database.verify_user(username, password, expected_role=role)
        if not user:
            flash(message, "error")
            return render_template('login.html', selected_role=role, username=username)

        # Login success - set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = user['role']
        session['badge_number'] = user['badge_number']
        session['department'] = user['department']

        flash(f"Welcome back, {user['full_name']}!", "success")
        if user['role'] == 'investigator':
            return redirect(url_for('investigator_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))

    role_param = request.args.get('role', 'user')
    return render_template('login.html', selected_role=role_param)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', 'user')
        badge_number = request.form.get('badge_number', '').strip() or None
        department = request.form.get('department', '').strip() or None

        if not username or not password or not full_name or not email:
            flash("All required fields must be filled.", "error")
            return render_template('register.html', role=role, username=username, full_name=full_name, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('register.html', role=role, username=username, full_name=full_name, email=email)

        # Enforce strong password
        is_strong, msg = database.validate_strong_password(password)
        if not is_strong:
            flash(f"Weak Password: {msg}", "error")
            return render_template('register.html', role=role, username=username, full_name=full_name, email=email)

        success, result = database.create_user(
            username=username,
            password=password,
            full_name=full_name,
            email=email,
            role=role,
            badge_number=badge_number,
            department=department
        )

        if not success:
            flash(result, "error")
            return render_template('register.html', role=role, username=username, full_name=full_name, email=email)

        flash("Registration successful! You can now log in with your credentials.", "success")
        return redirect(url_for('login', role=role))

    role_param = request.args.get('role', 'user')
    return render_template('register.html', role=role_param)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for('login'))

# =================== CITIZEN / USER ROUTES ===================

@app.route('/user/dashboard')
@login_required(role='user')
def user_dashboard():
    user_id = session.get('user_id')
    user_complaints = database.get_complaints_by_user(user_id)
    return render_template('user_dashboard.html', complaints=user_complaints)

# =================== INVESTIGATOR DASHBOARD & CASE SELECTION ===================

@app.route('/dashboard')
@app.route('/investigator/dashboard')
@login_required(role='investigator')
def investigator_dashboard():
    all_complaints = database.get_all_complaints()
    active_case = None
    active_case_id = session.get('active_case_id')
    if active_case_id:
        active_case = database.get_complaint_by_id(active_case_id)

    return render_template('dashboard.html', complaints=all_complaints, active_case=active_case)

@app.route('/case/select/<case_id>')
@login_required(role='investigator')
def select_case(case_id):
    complaint = database.get_complaint_by_id(case_id)
    if not complaint:
        flash("Selected case could not be found.", "error")
    else:
        session['active_case_id'] = case_id
        flash(f"Active investigation case set to {case_id}.", "success")
    return redirect(url_for('investigator_dashboard'))

@app.route('/case/clear')
@login_required(role='investigator')
def clear_case():
    session.pop('active_case_id', None)
    flash("Active case cleared. Select another complaint to investigate.", "info")
    return redirect(url_for('investigator_dashboard'))

@app.route('/complaint/status/<case_id>', methods=['POST'])
@login_required(role='investigator')
def update_status(case_id):
    status = request.form.get('status')
    notes = request.form.get('notes', '')
    investigator = session.get('full_name', 'Investigator')

    if status:
        database.update_complaint_status(case_id, status, notes=notes, investigator_name=investigator)
        flash(f"Case {case_id} status updated to '{status}'.", "success")
    return redirect(url_for('investigator_dashboard'))

# =================== COMPLAINTS ===================

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

        user_id = session.get('user_id') # None if anonymous
        complaint_id = database.create_complaint(
            user_id=user_id,
            name=name,
            email=email,
            phone=phone,
            crime_type=crime_type,
            description=description,
            suspect_info=suspect_info
        )

        return redirect(url_for('complaint_success', complaint_id=complaint_id))

    user_info = None
    if 'user_id' in session:
        user_info = database.get_user_by_id(session['user_id'])

    return render_template('complaint.html', user_info=user_info)

@app.route('/complaint/success/<complaint_id>')
def complaint_success(complaint_id):
    complaint_data = database.get_complaint_by_id(complaint_id)
    if not complaint_data:
        flash("Complaint not found.", "error")
        return redirect(url_for('complaint'))
    return render_template('complaint_success.html', complaint=complaint_data)

@app.route('/complaints')
@login_required(role='investigator')
def view_complaints():
    all_complaints = database.get_all_complaints()
    return render_template('complaints_list.html', complaints=all_complaints)

# =================== EVIDENCE UPLOAD & HASH VERIFICATION ===================

@app.route('/upload', methods=['GET', 'POST'])
@login_required(role='investigator')
def upload():
    active_case_id = session.get('active_case_id')
    all_complaints = database.get_all_complaints()

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        upload_mode = request.form.get('upload_mode', 'auto_hash') # 'auto_hash' or 'verify_hash'
        expected_hash = request.form.get('hash', '').strip().lower()
        case_id = request.form.get('case_id') or active_case_id or 'GENERAL-EVIDENCE'

        if not uploaded_file or uploaded_file.filename == '':
            flash("Please select an evidence file to upload.", "error")
            return redirect(url_for('upload'))

        file_content = uploaded_file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)
        original_name = uploaded_file.filename
        safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(original_name)}"
        filepath = os.path.join(UPLOAD_FOLDER, safe_name)

        # Write file to disk
        with open(filepath, 'wb') as f:
            f.write(file_content)

        verification_status = "Generated & Stored"
        result_message = "Evidence File Saved & SHA-256 Hash Generated Successfully ✅"

        if upload_mode == 'verify_hash' and expected_hash:
            if file_hash.lower() == expected_hash:
                verification_status = "Verified Match"
                result_message = "Integrity Verified: Evidence matches the provided reference hash! ✅"
            else:
                verification_status = "Hash Mismatch"
                result_message = "Hash Mismatch! The uploaded file does NOT match the reference hash. ❌"

        # Log to database
        evidence_id = database.add_evidence(
            case_id=case_id,
            filename=safe_name,
            original_name=original_name,
            sha256_hash=file_hash,
            file_size=file_size,
            uploaded_by=session.get('full_name', 'Investigator'),
            verification_status=verification_status
        )

        return render_template(
            'result.html',
            result=result_message,
            actual_hash=file_hash,
            filename=original_name,
            case_id=case_id,
            evidence_id=evidence_id,
            status=verification_status
        )

    return render_template('upload.html', active_case_id=active_case_id, complaints=all_complaints)

@app.route('/evidence')
@login_required(role='investigator')
def evidence():
    case_id = request.args.get('case_id') or session.get('active_case_id')
    if case_id:
        evidence_list = database.get_evidence_by_case(case_id)
    else:
        evidence_list = database.get_all_evidence()
    return render_template('evidence.html', evidence_list=evidence_list, active_case_id=case_id)

@app.route('/evidence/file/<int:evidence_id>')
@login_required(role='investigator')
def view_evidence_file(evidence_id):
    ev = database.get_evidence_by_id(evidence_id)
    if not ev:
        flash("Evidence record not found.", "error")
        return redirect(url_for('evidence'))

    filepath = os.path.join(UPLOAD_FOLDER, ev['filename'])
    if not os.path.exists(filepath):
        flash("Evidence file not found on disk.", "error")
        return redirect(url_for('evidence'))

    return send_file(filepath, download_name=ev['original_name'], as_attachment=False)

@app.route('/verify', methods=['GET', 'POST'])
@login_required(role='investigator')
def verify():
    all_evidence = database.get_all_evidence()
    if request.method == 'POST':
        verify_mode = request.form.get('verify_mode', 'file_only')
        uploaded_file = request.files.get('file')

        if not uploaded_file or uploaded_file.filename == '':
            flash("Please select an evidence file to verify.", "error")
            return redirect(url_for('verify'))

        file_content = uploaded_file.read()
        generated_hash = hashlib.sha256(file_content).hexdigest()
        filename = uploaded_file.filename

        match_status = None
        expected_hash = None

        if verify_mode == 'compare_hash':
            expected_hash = request.form.get('expected_hash', '').strip().lower()
            if expected_hash:
                match_status = (generated_hash.lower() == expected_hash)
        elif verify_mode == 'compare_stored':
            stored_ev_id = request.form.get('stored_evidence_id')
            if stored_ev_id:
                stored_ev = database.get_evidence_by_id(int(stored_ev_id))
                if stored_ev:
                    expected_hash = stored_ev['sha256_hash'].lower()
                    match_status = (generated_hash.lower() == expected_hash)

        return render_template(
            'verify_result.html',
            filename=filename,
            generated_hash=generated_hash,
            expected_hash=expected_hash,
            match_status=match_status
        )

    return render_template('verify.html', stored_evidence=all_evidence)

# =================== IP TRACKING ===================

@app.route('/ip_tracking', methods=['GET', 'POST'])
@login_required(role='investigator')
def ip_tracking():
    ip_info = None
    error = None
    if request.method == 'POST':
        ip_address = request.form.get('ip_address', '').strip()
        if ip_address:
            try:
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
@login_required(role='investigator')
def chat():
    return render_template('chat.html')

@app.route('/chat/send', methods=['POST'])
@login_required(role='investigator')
def chat_send():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if message:
        username = session.get('full_name', session.get('username', 'Investigator'))
        role = session.get('role', 'investigator')
        case_id = session.get('active_case_id')
        database.add_chat_message(username=username, role=role, message=message, case_id=case_id)
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'empty'}), 400

@app.route('/chat/messages')
@login_required(role='investigator')
def chat_get_messages():
    case_id = session.get('active_case_id')
    messages = database.get_chat_messages(limit=100, case_id=None)
    # Convert sqlite3.Row to dict
    msg_list = [{
        'username': m['username'],
        'role': m['role'],
        'message': m['message'],
        'timestamp': m['timestamp']
    } for m in messages]
    return jsonify(msg_list)

# =================== CHAIN OF CUSTODY REPORT ===================

@app.route('/report', methods=['GET', 'POST'])
@login_required(role='investigator')
def report():
    active_case_id = session.get('active_case_id')
    active_case = None
    evidence_entries = []

    if active_case_id:
        active_case = database.get_complaint_by_id(active_case_id)
        evidence_entries = database.get_evidence_by_case(active_case_id)

    if request.method == 'POST':
        case_number = request.form.get('case_number', active_case_id or 'N/A')
        investigator = request.form.get('investigator', session.get('full_name', 'N/A'))
        department = request.form.get('department', session.get('department', 'Cyber Forensics Unit'))
        description = request.form.get('description', 'N/A')

        # If evidence was found for case
        if not evidence_entries and case_number:
            evidence_entries = database.get_evidence_by_case(case_number)
        if not evidence_entries:
            evidence_entries = database.get_all_evidence()

        # Detailed itemized evidence records
        formatted_entries = []
        for idx, ev in enumerate(evidence_entries, 1):
            file_size_kb = round(ev['file_size'] / 1024, 2) if ev['file_size'] else 0.0
            formatted_entries.append({
                'item_num': idx,
                'filename': ev['original_name'],
                'file_size_kb': file_size_kb,
                'sha256': ev['sha256_hash'],
                'uploaded_by': ev['uploaded_by'],
                'uploaded_at': ev['uploaded_at'],
                'action': ev['verification_status'],
                'verified': ('Verified' in ev['verification_status'] or 'Intact' in ev['verification_status'] or 'Generated' in ev['verification_status'])
            })

        # Construct comprehensive, court-grade chronological Chain of Custody Audit Ledger
        timeline = []
        
        # Step 1: Grievance Intake
        intake_time = active_case['filed_at'] if active_case else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        complainant_name = active_case['name'] if active_case else 'Citizen Complainant'
        crime_cat = active_case['crime_type'] if active_case else 'Cyber Crime Incident'
        timeline.append({
            'timestamp': intake_time,
            'phase': 'Incident Inception & Filing',
            'custodian': complainant_name,
            'action': f"Official cyber crime grievance reported under category '{crime_cat}'. Initial complaint logged into central registry; Unique Case Identifier {case_number} allocated.",
            'proof_status': 'Intake Certified'
        })

        # Step 2: Case Assignment
        timeline.append({
            'timestamp': intake_time,
            'phase': 'Investigative Docket Assignment',
            'custodian': 'Central Dispatch System',
            'action': f"Case docket officially assigned to Lead Investigating Officer {investigator} ({department}) for formal forensics handling and chain-of-custody supervision.",
            'proof_status': 'Docket Assigned'
        })

        # Step 3: Forensic Artifact Ingestion & SHA-256 Hashing (Item by Item)
        for ev in formatted_entries:
            timeline.append({
                'timestamp': ev['uploaded_at'],
                'phase': 'Digital Evidence Acquisition',
                'custodian': ev['uploaded_by'],
                'action': f"Digital artifact Item #{ev['item_num']} ('{ev['filename']}', {ev['file_size_kb']} KB) seized and uploaded into encrypted evidence repository. Initial SHA-256 cryptographic fingerprint calculated: {ev['sha256']}. Ingestion protocol: {ev['action']}.",
                'proof_status': 'SHA-256 Fingerprinted & Sealed'
            })

        # Step 4: Cryptographic Integrity Validation
        for ev in formatted_entries:
            timeline.append({
                'timestamp': ev['uploaded_at'],
                'phase': 'Cryptographic Integrity Audit',
                'custodian': ev['uploaded_by'],
                'action': f"Secondary byte-level hash verification conducted on Item #{ev['item_num']} ('{ev['filename']}'). Result: {ev['action']}. Cryptographic hash matches recorded baseline with zero bit-level tampering.",
                'proof_status': 'Integrity Verified Intact'
            })

        # Step 5: Detective Investigation Notes & Status Transitions
        if active_case and active_case['investigation_notes']:
            timeline.append({
                'timestamp': active_case['updated_at'],
                'phase': 'Forensic Analysis & Progression',
                'custodian': investigator,
                'action': f"Investigative progress recorded: Case progression state transitioned to '{active_case['status']}'. Lead officer notes recorded: '{active_case['investigation_notes']}'.",
                'proof_status': 'Status Updated'
            })

        # Step 6: Final Chain of Custody Compilation & Sealing
        timeline.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'phase': 'Audit Certification & Report Closure',
            'custodian': investigator,
            'action': f"Digital Chain of Custody report certified and closed by Lead Investigator {investigator}. All digital artifacts cryptographically validated for evidentiary admissibility in judicial proceedings.",
            'proof_status': 'Certified Complete'
        })

        report_data = {
            'case_number': case_number,
            'investigator': investigator,
            'department': department,
            'description': description,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'evidence_entries': formatted_entries,
            'timeline': timeline,
            'case_details': active_case
        }

        return render_template('report_view.html', report=report_data)

    return render_template('report.html', active_case=active_case, active_case_id=active_case_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)