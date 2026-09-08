# 🦁 ElevateIQ Meet — Enterprise Video Conferencing & Real-Time Workspace Platform

[![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20Android%20APK-cyan.svg)](https://github.com/bathikadileep/elavateiqmeet)
[![Framework](https://img.shields.io/badge/Frontend-React%2019%20%7C%20TypeScript%205.8-blue.svg)](https://react.dev)
[![Backend](https://img.shields.io/badge/Backend-Python%203.12%20%7C%20Flask%203.0-green.svg)](https://flask.palletsprojects.org)
[![Database](https://img.shields.io/badge/Database-Neon%20PostgreSQL-indigo.svg)](https://neon.tech)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

**ElevateIQ Meet** is an enterprise-grade, ultra-low latency video conferencing, real-time collaboration, and workspace meeting platform. It provides seamless cross-device communication across desktop browsers and native Android smartphones, powered by WebRTC P2P Mesh, Socket.IO gateways, Flask Python backend, and React 19 glassmorphism UI.

---

## 🏗️ System Architecture

```
                                  ┌────────────────────────────────┐
                                  │   ElevateIQ Meet Client Apps   │
                                  ├───────────────┬────────────────┤
                                  │  Web Browser  │ Android Native │
                                  │  (React 19)   │ (.APK/Capacitor│
                                  └───────┬───────┴────────┬───────┘
                                          │                │
                         WebSocket / REST │                │  Public HTTPS / WSS
                                          ▼                ▼
                      ┌────────────────────────────────────────────────────────┐
                      │          Cloudflare Public HTTPS/WSS Tunnel            │
                      └──────────────────────────┬─────────────────────────────┘
                                                 │
                                                 ▼
                      ┌────────────────────────────────────────────────────────┐
                      │            ElevateIQ Flask Python Backend              │
                      │            (Port 5001 / Eventlet & Threading)          │
                      ├──────────────────────────┬─────────────────────────────┤
                      │ Blueprints:              │ Sockets:                    │
                      │  - Auth (JWT/Bcrypt)     │  - WebRTC Mesh Signaling    │
                      │  - Meetings Lifecycle    │  - P2P Video/Audio Relays   │
                      │  - AI Summarizer & Capt  │  - Real-Time Public Chat    │
                      │  - Security & GDPR Audit │  - Vector Whiteboard Sync   │
                      │  - SSO & Compliance      │  - Live Polling & Telemetry │
                      └──────────────────────────┴───────────────┬─────────────┘
                                                                 │
                                                                 ▼
                                      ┌────────────────────────────────────┐
                                      │     Neon Cloud Serverless DB       │
                                      │      (PostgreSQL 16 with SSL)      │
                                      └────────────────────────────────────┘
```

---

## ✨ Features & Capabilities

- 🎥 **Ultra-Low Latency WebRTC Video/Audio:** Hardware-accelerated P2P mesh audio/video streams with resilient multi-tier fallback (HD 720p $\rightarrow$ standard $\rightarrow$ audio-only $\rightarrow$ video-only).
- 💬 **Real-Time Collaboration Suite:** Interactive vector whiteboard canvas, live in-meeting chat, speech-to-text closed captions, and live polling.
- 🤖 **AI Meeting Intelligence:** Executive meeting summary generator, key decision extractor, sentiment analytics, and 25-language subtitle translation.
- 🛡️ **Enterprise Security & Compliance:** Cryptographic SHA-256 hash-chained audit logging, GDPR Article 17 (Right to be Forgotten) & Article 20 data exports, and SAML 2.0 / OIDC SSO federation.
- 📱 **Native Android Integration:** Optimized Capacitor 8 Android runtime with auto-granted camera/mic permissions, native share sheet, and gesture-free audio playback.

---

## 🛠️ Tech Stack

| Layer | Technology | Details |
|---|---|---|
| **Frontend** | React 19 + TypeScript 5.8 | Vite 8 bundler, Tailwind CSS 4, Lucide React icons |
| **Mobile** | Capacitor 8 (Android) | Native Java WebRTC bridge & custom `BridgeWebChromeClient` |
| **Backend** | Python 3.12 + Flask 3.0 | Flask-SocketIO (Eventlet / Threading) WSGI/ASGI |
| **Database** | Neon Cloud PostgreSQL / SQLite | SQLAlchemy 3.1 ORM with SSL pooling & Alembic migrations |
| **Media Stream** | WebRTC `RTCPeerConnection` | P2P mesh signaling over WebSockets |

---

## 🚀 Quick Start & Installation Guide

### Prerequisites
- **Python:** `v3.12` or higher
- **Node.js:** `v18` or `v20`+ (npm `v9`+)
- **Android SDK / Studio:** (Required only for building native Android `.apk`)

---

### Step 1: Clone Repository & Setup Virtual Environment

```bash
git clone https://github.com/bathikadileep/elavateiqmeet.git
cd elavateiqmeet

# Setup Python Virtual Environment
cd backend
python -m venv venv

# Activate Virtual Environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Backend Dependencies
pip install -r requirements.txt
```

---

### Step 2: Configure Environment Variables

Create a `.env` file inside the `backend/` directory:

```ini
FLASK_ENV=development
PORT=5001
SECRET_KEY=elevateiq-super-secret-production-key-12345
JWT_SECRET_KEY=jwt-secret-token-signature-key-67890
DATABASE_URL=sqlite:///elevateiq.db
# Optional: OpenAI / Gemini API Keys for LLM AI Summaries
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
```

Seed initial database test users:
```bash
python seed_users.py
```

---

### Step 3: Install & Start Frontend Development Server

Open a new terminal window:

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite Development Server
npm run dev
```

The frontend will start at `http://localhost:5173`.

---

### Step 4: Launch Backend API & Socket Server

In your backend terminal:

```bash
cd backend
python app.py
```

The backend server will start at `http://localhost:5001`.

---

## 🧪 Running Unit & Integration Tests

Run the complete backend test suite across all 18 API blueprints, database models, AI summarizers, and compliance engines:

```bash
cd backend
python -m unittest discover -s . -p "test_*.py"
```

To run individual module test suites:
```bash
# Compliance & Audit Hash Chaining Test
python -m unittest test_compliance.py

# Webinar & Breakout Suite Test
python -m unittest test_webinar.py

# AI Intelligence & Summaries Test
python -m unittest test_ai_intelligence.py
```

---

## 📱 Compiling the Native Android APK

To re-compile the native Android APK ([`ElevateIQ-Meet.apk`](file:///c:/Users/dilip/ELVIQ_MEET/ELVIQ%20MEET/ElevateIQ-Meet.apk)):

```powershell
# 1. Build the web bundle
cd frontend
npm run build

# 2. Sync web build into Capacitor Android project
npx cap sync android

# 3. Assemble Debug APK using Gradle
cd android
.\gradlew.bat assembleDebug

# 4. Copy output APK to project root
cd ..\..
Copy-Item "frontend\android\app\build\outputs\apk\debug\app-debug.apk" "ElevateIQ-Meet.apk" -Force
```

---

## 📡 REST API Route Overview

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/login` | `POST` | User login & JWT issuance |
| `/api/v1/meetings/create` | `POST` | Create instant/scheduled room |
| `/api/summaries/generate` | `POST` | Trigger AI meeting summary generation |
| `/api/compliance/export` | `GET` | Export GDPR Article 20 data ZIP bundle |
| `/api/compliance/forget` | `POST` | Execute GDPR Right to be Forgotten |
| `/api/webinar/qa/ask` | `POST` | Submit webinar Q&A question |
| `/api/telemetry/report` | `POST` | Submit WebRTC QoE network report |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.