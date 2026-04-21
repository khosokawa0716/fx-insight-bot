# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FX Compass** is an AI-driven FX trading system for USD_JPY and EUR_JPY pairs. It combines:
- Google Vertex AI (Gemini 1.5 Flash with Grounding + Google Search) for news sentiment analysis
- Technical indicators (MA20/50, RSI, MACD) for signal generation
- GMO Coin REST/WebSocket API for order execution with IFDOCO orders
- Cloud Firestore for persistence, Cloud Run for hosting, Cloud Scheduler for automation

## Commands

### Backend (Python/FastAPI)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Dev server (port 8000)
uvicorn src.main:app --reload --port 8000

# Run all tests
pytest

# Run a single test file
pytest tests/test_rule_engine.py

# Run with coverage
pytest --cov=core tests/

# Format + lint
black src/
ruff check src/
ruff check src/ --fix
```

### Frontend (React/TypeScript/Vite)

```bash
cd frontend

# Install and start dev server (port 5173, proxies /api → localhost:8000)
npm install
npm run dev

# Production build
npm run build
npm run preview
```

### Deployment

```bash
# Backend to Cloud Run
gcloud run deploy fx-insight-bot --source=backend/ --region=asia-northeast1
gcloud run deploy fx-insight-bot-exec --source=backend/ --region=asia-northeast1 --no-allow-unauthenticated

# Frontend to Firebase Hosting
firebase deploy --only hosting
```

## Architecture

### Core Data Flow

**News Collection** (triggered by Cloud Scheduler at 8:00 and 20:00 JST):
```
POST /api/v1/news/collect → NewsAnalyzer → Gemini Grounding (Google Search) → Firestore (news_events)
```

**Signal Generation** (on demand via GET /api/v1/signals):
```
GMO Coin klines → TechnicalAnalyzer (MA/RSI/MACD) + recent Firestore news
→ RuleEngine → scored BUY_CANDIDATE / SELL_CANDIDATE / IGNORE signals
```

**Trade Execution** (Cloud Scheduler at 9:00 and 21:00 JST, Mon–Fri):
```
POST /api/v1/trade/execute → RiskManager (daily P&L limit check + position sizing)
→ GMOCoinClient.place_ifdoco_order() → Firestore (trades)
→ Settlement check at 8:30 JST → update WIN/LOSS, actual_pnl
```

**Frontend Dashboard**:
```
React hooks (useAccount, useDashboardData, etc.) → fetch /api/v1/trade/* → display balance, positions, monthly P&L
```

### Two-Service Cloud Run Deployment

| Service | Endpoint access | Auth | Purpose |
|---------|----------------|------|---------|
| `fx-insight-bot` | Read-only routes | Public | Serves the Firebase-hosted dashboard |
| `fx-insight-bot-exec` | All routes incl. `/execute` | `cloud-scheduler-sa` only | Triggered by Cloud Scheduler |

### Backend Service Responsibilities

- **`news_analyzer.py`** — Calls Vertex AI Gemini with Google Search grounding; returns sentiment score (−1 to +1), impact score (0–1), directional signal
- **`rule_engine.py`** — Combines news signals with technical indicators to score trade candidates; see `docs/design/RULE_ENGINE_LOGIC.md` for scoring thresholds
- **`risk_manager.py`** — Enforces daily loss limits and lot-sizing rules before any order is placed
- **`trade_executor.py`** — Converts approved signals into IFDOCO orders (entry + stop-loss + take-profit in a single GMO API call)
- **`gmo_client.py`** — Handles REST and WebSocket communication with GMO Coin; rate limits and retry logic live here
- **`news_pipeline.py`** — Orchestrates the full collect → analyze → store cycle

### Frontend Conventions

- Each page in `src/pages/` has dedicated custom hooks in `src/hooks/` that wrap TanStack React Query
- `vite.config.ts` proxies `/api` to `localhost:8000`, so no CORS issues in development
- TypeScript interfaces for all API responses live in `src/types/index.ts`

## Configuration

**Backend** — copy `backend/.env.example` to `backend/.env`:
```
GCP_PROJECT_ID, GCP_LOCATION, FIRESTORE_DATABASE_ID
GOOGLE_APPLICATION_CREDENTIALS=../credentials/service-account.json
VERTEX_AI_MODEL=gemini-1.5-flash
ENVIRONMENT=development
```
GMO API keys are loaded from Cloud Secret Manager in production and must not be stored in `.env`.

**Frontend** — copy `frontend/.env.example` to `frontend/.env.local` with Firebase project credentials (`VITE_FIREBASE_*`).

**Firestore security rules** (`firestore.rules`) require `isAdmin()` for all reads/writes; direct client access from the frontend goes through Firebase Auth.

## Key Design Docs

Detailed algorithms and schemas are documented under `docs/design/`:
- `RULE_ENGINE_LOGIC.md` — full signal-scoring algorithm and thresholds
- `FIRESTORE_DESIGN.md` — collection schemas and index definitions
- `GMO_COIN_API_STRATEGY.md` — rate limits, WebSocket usage, order types
- `GEMINI_GROUNDING_EVALUATION.md` — why Gemini Grounding was chosen over alternatives
