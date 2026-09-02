# Developer Quickstart & Setup Guide

## Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Docker and Docker Compose (for PostgreSQL/pgvector)

---

## Local Environment Setup

### 1. Configure Environment File
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 2. Start PostgreSQL Container
```bash
make db-up
# Or manually:
docker-compose up -d postgres
```

### 3. Backend Setup & Local Server
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend API will be accessible at: `http://localhost:8000`  
Swagger API Docs available at: `http://localhost:8000/docs`

### 4. Frontend Setup & Dev Server
```bash
cd frontend
npm install
npm run dev
```
Frontend application shell will be accessible at: `http://localhost:3000`

---

## Verification & Testing Commands

### Backend Automated Test Suite
```bash
cd backend
pytest -v
```

### Frontend Type Check & Linter
```bash
cd frontend
npm run lint
npx tsc --noEmit
```

### Build Production Bundle
```bash
cd frontend
npm run build
```
