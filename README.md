# Cyber Crime Investigation & Evidence Management System

A web-based platform for cyber crime complaint filing, digital evidence handling with SHA-256 integrity verification, IP geolocation tracking, and chain-of-custody report generation.

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black?logo=flask)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **File Cyber Crime Complaints** — Submit detailed complaints with auto-generated case IDs
- **Digital Evidence Upload & Verification** — Upload files and verify integrity using SHA-256 hashes
- **SHA-256 Hash Generator** — Generate hash values for any file
- **IP Address Tracking** — Geolocate IP addresses (country, city, ISP, coordinates) via ip-api.com
- **Investigator Chat** — Real-time messaging system for team communication
- **Chain of Custody Reports** — Generate evidence reports with full audit trail
- **Evidence Locker** — Browse all uploaded evidence files
- **Investigator Dashboard** — Central hub for investigation tools

## Tech Stack

| Layer      | Technology                  |
|------------|-----------------------------|
| Backend    | Python, Flask               |
| Frontend   | HTML, CSS, JavaScript       |
| Hashing    | SHA-256 (hashlib)           |
| IP Lookup  | ip-api.com REST API         |
| UI Effects | Particles.js, Orbitron Font |

## Project Structure

```
CyberCrimeSystem/
├── app.py                  # Flask application (all routes & logic)
├── static/
│   └── css/
│       └── style.css       # Global styles
├── templates/
│   ├── index.html          # Landing page
│   ├── home.html           # Home page
│   ├── login.html          # Investigator login
│   ├── dashboard.html      # Investigator dashboard
│   ├── complaint.html      # File a complaint form
│   ├── complaint_success.html
│   ├── complaints_list.html
│   ├── upload.html         # Evidence upload & verify
│   ├── result.html         # Verification result
│   ├── verify.html         # Hash generator
│   ├── verify_result.html
│   ├── evidence.html       # Evidence locker
│   ├── ip_tracking.html    # IP geolocation tool
│   ├── chat.html           # Investigator chat
│   ├── report.html         # Report form
│   └── report_view.html    # Generated report view
└── uploads/                # Uploaded evidence files
```

## Getting Started

### Prerequisites

- Python 3.x

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/CyberCrimeSystem.git
   cd CyberCrimeSystem
   ```

2. **Install dependencies**
   ```bash
   pip install flask requests
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

## Usage

| Route             | Description                        |
|-------------------|------------------------------------|
| `/`               | Landing page                       |
| `/complaint`      | File a new cyber crime complaint   |
| `/complaints`     | View all filed complaints          |
| `/upload`         | Upload & verify digital evidence   |
| `/verify`         | Generate SHA-256 hash for a file   |
| `/evidence`       | Browse uploaded evidence files     |
| `/ip_tracking`    | Track/geolocate an IP address      |
| `/chat`           | Investigator chat room             |
| `/report`         | Generate chain-of-custody report   |
| `/dashboard`      | Investigator dashboard             |
| `/login`          | Investigator login                 |

## Screenshots

> Add screenshots of the landing page, dashboard, and key features here.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "Add your feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

---

> **Disclaimer:** This project is developed for educational and academic purposes. It is not intended for use in real law enforcement investigations.
