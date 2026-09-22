import sqlite3
import os
import re
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cybercrime.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def validate_strong_password(password: str):
    """
    Validates password strength:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_+=\[\]\\/]', password):
        return False, "Password must contain at least one special character (!@#$%^&* etc.)."
    return True, "Password is strong."

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'investigator')),
            badge_number TEXT,
            department TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    # Complaints table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            crime_type TEXT NOT NULL,
            description TEXT NOT NULL,
            suspect_info TEXT,
            status TEXT DEFAULT 'Pending',
            assigned_investigator TEXT,
            investigation_notes TEXT,
            filed_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Evidence table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            sha256_hash TEXT NOT NULL,
            file_size INTEGER,
            uploaded_by TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES complaints(id)
        )
    ''')

    # Chat messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    conn.commit()

    # Seed default sample accounts if users table is empty
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    if count == 0:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Default Investigator: investigator / Investigator@2026!
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, email, role, badge_number, department, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'investigator',
            generate_password_hash('Investigator@2026!'),
            'Senior Inspector V. Sharma',
            'investigator@cybercell.gov',
            'investigator',
            'CC-INV-9041',
            'Cyber Forensics & Crime Branch',
            now
        ))

        # Default Citizen: citizen / Citizen@2026!
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, email, role, badge_number, department, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'citizen',
            generate_password_hash('Citizen@2026!'),
            'Rohan Mehta',
            'rohan.mehta@example.com',
            'user',
            None,
            None,
            now
        ))

        # Sample initial complaint for testing
        cursor.execute('''
            INSERT INTO complaints (id, user_id, name, email, phone, crime_type, description, suspect_info, status, assigned_investigator, investigation_notes, filed_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'CYB-20260920-0001',
            2,
            'Rohan Mehta',
            'rohan.mehta@example.com',
            '+91 9876543210',
            'Financial Fraud / Phishing',
            'Received unauthorized OTP requests and ₹75,000 was debited via spoofed banking link.',
            'SMS sender ID: VM-HDFCBK, IP trace lead: 185.220.101.5',
            'Under Investigation',
            'Senior Inspector V. Sharma',
            'Initial IP trace logged. Evidence hashes pending verification.',
            '2026-09-20 14:30:00',
            '2026-09-20 16:00:00'
        ))

        conn.commit()

    conn.close()

# --- User Management ---

def create_user(username, password, full_name, email, role, badge_number=None, department=None):
    is_strong, msg = validate_strong_password(password)
    if not is_strong:
        return False, msg

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, email, role, badge_number, department, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username.strip(), password_hash, full_name.strip(), email.strip(), role, badge_number, department, now))
        conn.commit()
        user_id = cursor.lastrowid
        return True, user_id
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please choose a different username."
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE', (username.strip(),))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def verify_user(username, password, expected_role=None):
    user = get_user_by_username(username)
    if not user:
        return None, "Account not found. Please register first."
    if not check_password_hash(user['password_hash'], password):
        return None, "Incorrect password. Please try again."
    if expected_role and user['role'] != expected_role:
        return None, f"Unauthorized: Account is registered as '{user['role']}', not '{expected_role}'."
    return user, "Authentication successful."

# --- Complaints Management ---

def create_complaint(user_id, name, email, phone, crime_type, description, suspect_info=''):
    conn = get_db_connection()
    cursor = conn.cursor()

    clean_name = name.strip()
    clean_email = email.strip()
    clean_phone = phone.strip() if phone else ''
    clean_crime = crime_type.strip()
    clean_desc = description.strip()
    clean_suspect = suspect_info.strip() if suspect_info else ''

    # Check if an identical complaint has already been submitted to prevent duplicate records
    cursor.execute('''
        SELECT id FROM complaints 
        WHERE (email = ? OR name = ?) 
          AND crime_type = ? 
          AND description = ?
    ''', (clean_email, clean_name, clean_crime, clean_desc))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return existing['id']

    # Generate sequential unique Case ID for today
    today_prefix = f'CYB-{datetime.now().strftime("%Y%m%d")}-'
    cursor.execute('SELECT id FROM complaints WHERE id LIKE ? ORDER BY id DESC LIMIT 1', (f'{today_prefix}%',))
    last_row = cursor.fetchone()
    if last_row:
        try:
            last_num = int(last_row['id'].split('-')[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1

    complaint_id = f'{today_prefix}{new_num:04d}'
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO complaints (id, user_id, name, email, phone, crime_type, description, suspect_info, status, filed_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
    ''', (complaint_id, user_id, clean_name, clean_email, clean_phone, clean_crime, clean_desc, clean_suspect, now, now))
    conn.commit()
    conn.close()
    return complaint_id

def get_complaint_by_id(complaint_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,))
    complaint = cursor.fetchone()
    conn.close()
    return complaint

def get_complaints_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM complaints WHERE user_id = ? ORDER BY filed_at DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_complaints():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM complaints ORDER BY filed_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_complaint_status(complaint_id, status, notes='', investigator_name=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE complaints
        SET status = ?, investigation_notes = ?, assigned_investigator = ?, updated_at = ?
        WHERE id = ?
    ''', (status, notes.strip(), investigator_name.strip(), now, complaint_id))
    conn.commit()
    conn.close()

# --- Evidence Management ---

def add_evidence(case_id, filename, original_name, sha256_hash, file_size, uploaded_by, verification_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO evidence (case_id, filename, original_name, sha256_hash, file_size, uploaded_by, verification_status, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (case_id, filename, original_name, sha256_hash, file_size, uploaded_by, verification_status, now))
    conn.commit()
    evidence_id = cursor.lastrowid
    conn.close()
    return evidence_id

def get_evidence_by_id(evidence_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evidence WHERE id = ?', (evidence_id,))
    ev = cursor.fetchone()
    conn.close()
    return ev

def get_evidence_by_case(case_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evidence WHERE case_id = ? ORDER BY uploaded_at DESC', (case_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_evidence():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evidence ORDER BY uploaded_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- Chat Messages ---

def add_chat_message(username, role, message, case_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO chat_messages (case_id, username, role, message, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (case_id, username, role, message.strip(), now))
    conn.commit()
    conn.close()

def get_chat_messages(limit=100, case_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if case_id:
        cursor.execute('SELECT * FROM chat_messages WHERE case_id = ? ORDER BY id ASC LIMIT ?', (case_id, limit))
    else:
        cursor.execute('SELECT * FROM chat_messages ORDER BY id ASC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows
