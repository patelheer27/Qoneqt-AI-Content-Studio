# Multi-stage Dockerfile for Qoneqt AI Content Studio
# Stage 1: Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend & Runtime
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY .env.example ./.env

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure generated directories exist
RUN mkdir -p generated/images generated/audio generated/videos generated/captions

ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
