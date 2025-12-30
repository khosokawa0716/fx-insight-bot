# FX Insight Bot - Backend

FastAPI-based backend for FX news collection, AI analysis, and trading signals.

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Verify GCP Authentication

```bash
export GOOGLE_APPLICATION_CREDENTIALS="../credentials/service-account.json"
```

## Development

### Run Development Server

```bash
uvicorn src.main:app --reload --port 8000
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
ruff check src/
```

## Project Structure

```
backend/
├── src/
│   ├── models/        # Pydantic models & Firestore schemas
│   ├── services/      # Business logic (news collection, AI analysis)
│   ├── api/           # FastAPI routes
│   └── utils/         # Utilities (logging, config)
├── tests/             # Unit & integration tests
├── requirements.txt   # Python dependencies
└── .env              # Environment variables (not in git)
```

## Next Steps

1. Implement RSS news collection (Phase 2)
2. Add Vertex AI integration (Phase 3)
3. Create trading signal generation (Phase 4)
