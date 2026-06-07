# ── Stage 1: build the React frontend ────────────────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
# VITE_API_URL is empty → same-origin API calls (backend serves both)
RUN npm run build

# ── Stage 2: Python backend ───────────────────────────────────────────────────
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

# Bundle the sample databases (no volume mount needed)
COPY db/sample_dbs/ /data/

# Copy the built frontend so FastAPI can serve it as static files
COPY --from=frontend-build /frontend/dist ./frontend/dist

RUN mkdir -p /app/uploads /app/chroma_data

EXPOSE 8000

# Railway injects $PORT; fall back to 8000 locally
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
