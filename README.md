# Qoneqt AI Content Studio

> **Tagline:** *From One Idea to a Publish-Ready Video.*  
> **Repository:** [https://github.com/patelheer27/Qoneqt-AI-Content-Studio](https://github.com/patelheer27/Qoneqt-AI-Content-Studio)

---

## 1. Overview

**Qoneqt AI Content Studio** is an AI video generation studio enhanced with passwordless authentication, media integrity verification, and metadata sanitization:

1. **AI Video Generation Pipeline**:
   - **AI Script & Strategy Generation**: Powered by Groq LLM (`llama-3.3-70b-versatile`).
   - **AI Voiceover & Speech Synthesis**: High-fidelity narration with Edge-TTS and gTTS.
   - **Visual Asset Generation**: Full-bleed media processing with Pillow and Pollinations.
   - **FFmpeg Compositor**: Frame-accurate multi-scene rendering, transitions, and audio synchronization.
2. **Email + OTP Passwordless Authentication**:
   - Secure 6-digit cryptographic OTPs with 5-minute expiration, 60-second cooldown, and max-attempt limiting.
   - Keyed HMAC hash storage (never stored in plaintext).
   - Automatic first-time user account creation and returning-user session handling.
   - Configurable SMTP support with a local **Development OTP Demo Mode**.
3. **Video Integrity Checker**:
   - Real chunked SHA-256 cryptographic hashing of raw file bytes (memory-safe streaming up to 100 MB).
   - Byte-level fingerprint calculation and constant-time reference hash verification (`hmac.compare_digest`).
4. **Video Metadata Sanitizer**:
   - Deep container and stream metadata inspection using real native **FFprobe**.
   - Streamlined metadata stripping via **FFmpeg** (`-map_metadata -1 -map_chapters -1 -fflags +bitexact`) without overwriting the original file.
   - Structured before-and-after comparison table.
   - Authorized download endpoint for sanitized output files.
5. **Security & Privacy Center**:
   - Dedicated dashboard module with real session metrics, security cards, and tools.

---

## 2. Project Architecture & Directory Structure

```
Qoneqt_Ai_Content_Studio/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── project.py          # Video projects & storyboards
│   │   │   ├── user.py             # User, OTPRecord, SessionRecord
│   │   │   └── security.py         # MetadataJob, SecurityLog
│   │   ├── routes/
│   │   │   ├── projects.py         # Video generation routes
│   │   │   ├── auth.py             # OTP request, verify, me, logout
│   │   │   └── security.py         # Integrity hash/verify, inspect, sanitize, download
│   │   ├── schemas/
│   │   │   ├── project.py
│   │   │   ├── auth.py
│   │   │   └── security.py
│   │   ├── services/
│   │   │   ├── auth_service.py     # Cryptographic OTP, SMTP & session management
│   │   │   ├── integrity_service.py# Chunked SHA-256 byte streaming
│   │   │   ├── metadata_service.py # Native FFprobe inspection & FFmpeg sanitization
│   │   │   ├── llm_service.py      # Groq AI script generator
│   │   │   ├── tts_service.py      # Edge-TTS voice synthesis
│   │   │   └── video_service.py    # FFmpeg scene compositor
│   │   ├── config.py               # Pydantic Settings & environment variables
│   │   ├── database.py             # SQLAlchemy SQLite engine & session
│   │   └── main.py                 # FastAPI application & router mounts
│   ├── storage/
│   │   ├── assets/                 # Background visuals & audio clips
│   │   ├── renders/                # Rendered videos
│   │   │   └── sanitized/          # Sanitized video copies
│   │   └── temp/                   # Temporary upload working files
│   ├── tests/
│   │   └── test_enhanced_features.py # Automated test suite (13 passing tests)
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── context/
│   │   │   └── AuthContext.tsx     # Session state & auth provider
│   │   ├── services/
│   │   │   └── api.ts              # Axios client with session interceptors
│   │   ├── pages/
│   │   │   ├── Login.tsx           # Passwordless OTP login page
│   │   │   ├── SecurityCenter.tsx  # Security & Privacy Center (3 feature tabs)
│   │   │   ├── Dashboard.tsx       # Studio overview & quick action banner
│   │   │   ├── CreateVideo.tsx     # AI video creation studio
│   │   │   ├── Projects.tsx        # Project gallery & video downloads
│   │   │   ├── ProjectDetails.tsx  # Timeline editor & social captions
│   │   │   ├── Assets.tsx          # Uploaded & generated media assets
│   │   │   └── Templates.tsx       # Pre-built video templates
│   │   ├── App.tsx                 # Navigation, branding & auth routing
│   │   └── App.css
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
└── README.md
```

---

## 3. Environment Variables Configuration

Copy `backend/.env.example` to `backend/.env` and configure settings:

```ini
# --- LLM & AI Services ---
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
POLLINATIONS_API_KEY=

# --- Database & Runtime ---
DATABASE_URL=sqlite:///./video_studio.db
DEMO_MODE=false

# --- Security & Session ---
SECRET_KEY=qoneqt-ai-content-studio-super-secret-key-2026
SESSION_TTL_HOURS=24

# --- Email + OTP Authentication ---
OTP_TTL_SECONDS=300
OTP_RESEND_COOLDOWN_SECONDS=60
OTP_MAX_ATTEMPTS=5
OTP_DEMO_MODE=true

# --- Optional SMTP Settings ---
# If left blank, OTP_DEMO_MODE displays generated codes locally for demonstration
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@qoneqt.studio

# --- Media Security Limits ---
MAX_UPLOAD_SIZE_MB=100
FFMPEG_TIMEOUT_SECONDS=120
METADATA_RETENTION_HOURS=24
```

> **Note on Development Demo Mode:** When `SMTP_HOST` is not configured and `OTP_DEMO_MODE=true`, the backend securely generates and verifies real OTPs, but provides the code in the local dev response and console log so you can test the system locally without purchasing a third-party email provider. In production, setting `OTP_DEMO_MODE=false` disables dev code exposure.

---

## 4. Installation & Local Startup

### Prerequisites
- Python 3.10+
- Node.js 18+
- FFmpeg and FFprobe installed and available in system PATH

### Step 1: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend server on port 8000
uvicorn app.main:app --reload --port 8000
```
Backend API will be running at: `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

### Step 2: Frontend Setup

```bash
# Open a new terminal in the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend Web Studio will be running at: `http://localhost:5173`.

---

## 5. Automated Test Suite

Run the automated test suite using `pytest`:

```bash
cd backend
venv\Scripts\python -m pytest tests/test_enhanced_features.py -v
```

### Verified Test Cases:
| Test Name | Status | Description |
|:---|:---:|:---|
| `test_health` | **PASSED** | Validates API health check status |
| `test_otp_request_demo_mode` | **PASSED** | Tests 6-digit OTP generation and demo mode |
| `test_otp_resend_cooldown` | **PASSED** | Enforces 60-second resend rate-limiting |
| `test_otp_verify_invalid_code` | **PASSED** | Validates attempt increment on incorrect OTP |
| `test_otp_verify_success_and_user_creation` | **PASSED** | Automatic user creation on first successful login |
| `test_otp_verify_returning_user` | **PASSED** | Authenticates existing user on subsequent logins |
| `test_video_integrity_calculate_hash` | **PASSED** | Computes byte-exact SHA-256 hash |
| `test_video_integrity_verify_match` | **PASSED** | Verifies matching reference hash byte-for-byte |
| `test_video_integrity_verify_mismatch` | **PASSED** | Flags tampered or differing reference hashes |
| `test_video_integrity_invalid_reference_format` | **PASSED** | Rejects malformed reference hash strings |
| `test_video_metadata_inspect` | **PASSED** | Extracts container and stream metadata via FFprobe |
| `test_video_metadata_sanitize_and_download` | **PASSED** | Strips metadata via FFmpeg and enables download |
| `test_security_stats` | **PASSED** | Queries operational session verification metrics |

---

## 6. Live Demonstration Guide (College Faculty Presentation)

### Demo 1: Passwordless Email + OTP Login
1. Open the application in your browser at `http://localhost:5173`.
2. Notice that unauthenticated requests are automatically directed to the **Qoneqt Welcome & Sign-In Page**.
3. Enter any email address (e.g. `faculty@qoneqt.studio`) and click **Send OTP**.
4. The system:
   - Validates the email format.
   - Generates a cryptographically secure 6-digit OTP on the backend.
   - Stores a keyed HMAC hash in SQLite (no plaintext storage).
   - Starts the 5-minute expiration countdown and 60-second cooldown.
   - In Development Mode, presents the code directly on the screen with an **Auto-fill Code** button.
5. Click **Auto-fill Code** (or paste the code) and click **Verify OTP**.
6. **Result**: The backend validates the code, marks it as used (single-use), automatically provisions the user account, establishes a 24-hour authenticated session, and redirects to the dashboard.
7. Click the **Log Out** button in the sidebar to demonstrate that session invalidation works.

### Demo 2: Video Integrity Checker (SHA-256)
1. Sign in and click **Security Center** from the sidebar navigation (or the Dashboard banner).
2. Select the **Video Integrity Checker** tab.
3. Upload any MP4 video file.
4. Click **Calculate SHA-256**:
   - The backend streams the file in 64 KB chunks, without loading the full file into memory.
   - The calculated SHA-256 hexadecimal hash is displayed with the exact byte count.
5. Click **Copy Hash** to copy the reference fingerprint to your clipboard.
6. Paste the copied hash into the **Verify Against Reference SHA-256 Hash** input.
7. Click **Verify Integrity**:
   - Displays **Integrity Verified — SHA-256 hashes match** (Green alert).
8. Change a single character in the reference hash and click **Verify Integrity**:
   - Displays **Integrity Mismatch — SHA-256 hashes differ** (Amber alert).
9. Explain the security note: *"SHA-256 verifies byte-level equality against a reference; it does not determine whether content was synthesized or trustworthy initially."*

### Demo 3: Video Metadata Sanitizer (FFprobe & FFmpeg)
1. In the **Security & Privacy Center**, select the **Video Metadata Sanitizer** tab.
2. Select a video file and click **Inspect Metadata**:
   - The backend runs **FFprobe** in safe argument-list mode.
   - Displays detected container format, duration, dimensions, video/audio codecs, creation timestamps, and encoder tags.
3. Click **Sanitize Video**:
   - The backend invokes **FFmpeg** with `-map_metadata -1 -map_chapters -1 -fflags +bitexact`.
   - Strips identifying tags into a new separate sanitized video file (the original file is never overwritten).
   - Inspects the output file with FFprobe and presents a structured **Before vs. After Metadata Comparison** table showing removed tags and preserved video/audio streams.
4. Click **Download Sanitized Video** to download the cleaned MP4 copy via the authorized download route.

### Sample Video Generation Command for Testing
To generate a 1-second test video with custom tags:
```bash
ffmpeg -y -f lavfi -i testsrc=size=320x240:rate=10 -f lavfi -i sine=frequency=1000:duration=1 -t 1 -metadata title="Qoneqt Demonstration" -metadata author="Faculty Presenter" -metadata comment="Sensitive Tag" -c:v libx264 -preset ultrafast -c:a aac demo_test.mp4
```

---

## 7. Security Architecture & Safeguards

- **Cryptographic OTPs**: Uses Python `secrets.randbelow` for unguessable 6-digit codes.
- **Keyed Hash Storage**: OTP codes are salted and hashed using `hmac.new(..., hashlib.sha256)`. Plaintext OTPs never touch the database.
- **Single-Use & Invalidation**: Used OTPs cannot be re-verified; requesting a new code invalidates prior active codes.
- **Memory-Safe File Streaming**: 64 KB chunked read prevents Out-Of-Memory (OOM) Denial-of-Service attacks.
- **Safe Subprocess Execution**: Native FFprobe and FFmpeg commands execute via explicit argument lists without shell interpolation (`check=False`, `shell=False`).
- **Path Traversal Protection**: Uploaded files and sanitized outputs use server-generated UUID filenames.
