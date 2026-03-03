# FastAPI MySQL API

FastAPI + SQLAlchemy + MySQL. Platform-integration endpoints (Meta OAuth, status, revoke).

## Setup

```sh
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Optional: `export DATABASE_URL="mysql+mysqlconnector://user:pass@localhost:3306/meta_poc"`

## Run

1. Start MySQL and create DB: `CREATE DATABASE IF NOT EXISTS meta_poc;` (or run `scripts/init_meta_poc.sql`).
2. Start API:
   ```sh
   cd api && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 5005
   ```
   → **http://localhost:5005**

#Run ngrok
ngrok http --url=clumplike-oswaldo-dowily.ngrok-free.dev 5005

## Endpoints (v1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/platform-integration/status/{workspace_id}` | List integrations |
| POST | `/v1/platform-integration/meta/auth` | Meta OAuth URL. Body: `{"workspace_id": N}` |
| POST | `/v1/platform-integration/revoke-access` | Revoke. Body: `{"workspace_id": N, "tokenRecord_id": N}` |
| POST | `/v1/platform-data/set-platform-data` | Set data. Body: `{"workspace_id": N, "data": {...}}` |
| POST | `/v1/platform-data/get-platform-data` | Run Meta ETL. Body: `{"workspace_id": N}`. Returns `{ success, workspace_id, data }`. |

Env: `META_ADS_CLIENT_ID`, `META_ADS_CLIENT_SECRET`, `META_ADS_REDIRECT_URI`, `BASE_APP_UI_URL`.
