# Qoneqt AI Content Studio

An AI-driven video and content generation studio powered by FastAPI and React.

## Overview

Qoneqt AI Content Studio streamlines end-to-end video and content production:
- **AI Script Generation**: Powered by Groq LLM (`llama-3.3-70b-versatile`).
- **AI Voiceover & Narration**: High quality speech synthesis with Edge-TTS and gTTS.
- **Visual Assets & Media**: Image and asset processing with Pillow and Pollinations.
- **Studio Interface**: Modern React + TypeScript + Vite frontend with dashboard, script generator, timeline editor, and project management.

---

## Project Structure

```
├── backend/
│   ├── app/                # FastAPI application and route handlers
│   ├── storage/            # Local assets, renders, and project temp data
│   ├── .env.example        # Environment variable template
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/                # React components, pages, and styling
│   ├── package.json        # Frontend dependencies & scripts
│   └── vite.config.ts      # Vite configuration
└── README.md
```

---

## Getting Started

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Configure your API keys in .env
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

Configure the following in `backend/.env`:
- `GROQ_API_KEY`: Your Groq API key for script generation.
- `GROQ_MODEL`: Model name (default: `llama-3.3-70b-versatile`).
- `DATABASE_URL`: SQLite or PostgreSQL database URL.
- `DEMO_MODE`: Set to `true` or `false`.
