<div align="center">

# 🛰️ IP Tracker

### A Professional Flask-Based IP & Browser Telemetry Demonstration Tool

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-000000?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![MIT License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue?style=for-the-badge)]()
[![Security](https://img.shields.io/badge/Purpose-Authorized%20Security%20Testing-red?style=for-the-badge)]()
[![Maintained](https://img.shields.io/badge/Maintained-Yes-success?style=for-the-badge)]()

*A cybersecurity demonstration project for collecting IP geolocation and browser telemetry in **authorized** security assessments, laboratory exercises, and educational environments.*

</div>

---

# ⚠️ Legal Notice

> **This project is intended exclusively for authorized cybersecurity activities.**

Use this software **only** when you have explicit permission from the owner of the system or participant.

**Never use this project for:**

- Unauthorized tracking
- Phishing campaigns
- Stalking
- Harassment
- Doxxing
- Surveillance
- Privacy violations
- Identity discovery
- Illegal data collection

The author assumes **no responsibility** for misuse.

---

# ✨ Features

## 🌍 Network Intelligence

- Public IP detection
- Country identification
- Region & State lookup
- City detection
- Postal code lookup
- Latitude & Longitude
- Timezone detection

---

## 🛰️ Geolocation

- Local MaxMind GeoLite2 database support
- Online IP enrichment
- ISP detection
- ASN lookup
- Organization identification
- Network provider information

---

## 📱 Browser Fingerprinting

Collects browser metadata such as:

- Browser name
- Browser version
- Operating System
- Device type
- Platform
- User-Agent
- Language
- Screen resolution
- Timezone
- Device capabilities

---

## 📍 GPS Collection (Optional)

If the browser supports Geolocation API **and** the participant grants permission:

- GPS Latitude
- GPS Longitude
- Accuracy
- Timestamp

Otherwise the application automatically falls back to IP-based geolocation.

---

## 📝 Logging

Every visit is logged in JSONL format.

```
logs/
└── YYYY-MM-DD.jsonl
```

Each event includes:

- Timestamp
- IP
- Browser details
- Geolocation
- GPS (if permitted)
- Network metadata


---

# 🚀 Installation

Clone the repository

```bash
git clone https://github.com/USERNAME/IP-Tracker.git

cd IP-Tracker
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🌍 GeoLite2 Database

Download the **GeoLite2 City** database from MaxMind.

https://www.maxmind.com/en/geolite2/signup

Place

```
GeoLite2-City.mmdb
```

inside the project folder.

Directory example

```
IP-Tracker/

GeoLite2-City.mmdb
1.py
README.md
```

---

# ⚙️ Configuration

Inside `1.py`

```python
YOUTUBE_URL = "https://www.youtube.com/watch?v=F17CBysnRso"

GEO_DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "GeoLite2-City.mmdb"
)

LOG_DIR = "logs"
```

For local testing

```python
app.run(
    host="127.0.0.1",
    port=5000
)
```

Avoid exposing the development server directly to the Internet.

---

# ▶️ Running

```bash
python 1.py
```

Open

```
http://127.0.0.1:5000
```

---

# 📊 Information Collected

Depending on browser support and participant consent:

| Category | Information |
|-----------|-------------|
| Network | IP Address |
| Geo | Country |
| Geo | Region |
| Geo | City |
| Geo | Postal Code |
| Geo | Latitude |
| Geo | Longitude |
| Geo | Timezone |
| ISP | ISP Name |
| ISP | ASN |
| ISP | Organization |
| Browser | Browser Name |
| Browser | Browser Version |
| Browser | Operating System |
| Browser | Device Type |
| Browser | User-Agent |
| Browser | Language |
| Browser | Screen Size |
| Browser | Platform |
| Browser | Timezone |
| Browser | Device Capabilities |
| GPS | Latitude *(Permission Required)* |
| GPS | Longitude *(Permission Required)* |
| GPS | Accuracy |

---

# 🔐 Security Recommendations

For authorized deployments:

- HTTPS only
- Authentication
- Authorization
- Reverse Proxy
- Input Validation
- Rate Limiting
- Request Size Limits
- Secure Log Storage
- Data Retention Policy
- Regular Dependency Updates

Never trust:

- X-Forwarded-For
- Client supplied headers
- Browser fingerprint alone

---

# 📚 Educational Use Cases

Suitable for:

- Cybersecurity Labs
- Security Awareness Demonstrations
- Web Security Classes
- Browser Privacy Demonstrations
- Geolocation Demonstrations
- Network Security Exercises
- Blue Team Training
- Red Team Simulations *(with authorization)*

---

# 📄 Logging Example

```json
{
  "timestamp":"2026-08-01T10:52:41Z",
  "ip":"203.0.113.15",
  "country":"India",
  "city":"Delhi",
  "browser":"Chrome",
  "os":"Windows 11",
  "gps":null
}
```

---

# ⚠️ Privacy

This application processes personal information.

Before collecting any information, participants should be informed of:

- What data is collected
- Why it is collected
- Where it is stored
- Who can access it
- How long it is retained
- How it can be deleted

GPS information is collected **only after explicit browser permission is granted.**

---

# 📜 License

This project is licensed under the **MIT License**.

Third-party services and datasets remain under their respective licenses.

- MaxMind GeoLite2
- ip-api.com
- OpenStreetMap / Nominatim

---

# 👨‍💻 Author

## Dharmpreet Singh (Gh0$t)

Cybersecurity Researcher

Offensive Security • Web Application Security • AI Security • Red Teaming

---

<div align="center">

### ⭐ If you found this project useful, consider giving it a Star.

*"Knowledge is most valuable when used responsibly."*

</div>
