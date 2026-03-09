# FastAPI MySQL API

FastAPI + SQLAlchemy + MySQL. Meta POC with **Platform Integration** (Meta OAuth, status, revoke) and **Platform Data** (Meta ETL, stored in `platform_data` table).

## Setup

```sh
cd api
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Environment (optional):**

- `DATABASE_URL` – **MySQL** connection string, e.g.  
  `mysql+mysqlconnector://user:pass@localhost:3306/meta_poc`  
  (If set to an MSSQL/SQL Server URL, it is ignored and the default MySQL URL or `MYSQL_DATABASE_URL` is used.)
- `MYSQL_DATABASE_URL` – MySQL URL used when `DATABASE_URL` is not MySQL (optional).
- `META_ADS_CLIENT_ID`, `META_ADS_CLIENT_SECRET`, `META_ADS_REDIRECT_URI`, `BASE_APP_UI_URL` – for Meta OAuth and redirects
- `META_API_VERSION` – Meta Graph API version (default `v23.0`)
- `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_AUTH_REDIRECT_URI` – for Google Ads OAuth (ref: nyx-api)

## Run

1. **Initialize database (run `init_poc.sql`):**
   - From the **api** directory:
     ```sh
     cd api
     mysql -u root -p < scripts/init_poc.sql
     ```
   - Or from the **project root** (`meta-poc`):
     ```sh
     mysql -u root -p < api/scripts/init_poc.sql
     ```
   - You will be prompted for the MySQL root password. This creates the `meta_poc` database and tables (`integration`, `platform_data`).
   - **Alternative:** If MySQL is already running and you have a different user:
     ```sh
     mysql -u YOUR_USER -p -h localhost < api/scripts/init_poc.sql
     ```

2. **API:**
   ```sh
   cd api && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 5005
   ```
   → **http://localhost:5005**
   - If you did not run the SQL script, ensure the database exists (`CREATE DATABASE meta_poc;`); the app will create tables on startup via SQLAlchemy `create_all`.

3. **Docs:** Swagger UI at **http://localhost:5005/docs**

## Endpoints (v1)

### Platform Integration

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/campaign-ads/status` | List integrations (workspace 1) |
| POST | `/v1/campaign-ads/meta/auth` | Get Meta OAuth URL |
| GET | `/v1/campaign-ads/meta/auth/callback` | OAuth callback (Meta redirects here) |
| POST | `/v1/campaign-ads/google/auth` | Get Google Ads OAuth URL |
| GET | `/v1/campaign-ads/google/auth/callback` | OAuth callback (Google redirects here) |
| POST | `/v1/campaign-ads/revoke-access` | Revoke integration. Body: `{"integration_id": N}` |

### Platform Data

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/platform-data/platform-data` | Get or set `platform_data`. **Set:** Body `{"workspace_id": N, "data": {"campaigns": [...]}}`. **Get:** Body `{"workspace_id": N}` (no `data`). Returns `{ success, workspace_id }` on set, or `{ success, workspace_id, data: { campaigns } }` on get. |
| POST | `/v1/platform-data/run-meta-etl` | Run Meta ETL (extract → transform → load), save to `platform_data` table, return data. Body: `{"workspace_id": N}` |

## Database

- **Tables:** `integration`, `platform_data`
- **platform_data:** One row per workspace; column `campaigns` (JSON). Meta ETL persists only campaigns (see `meta_extractor/config.py`).

## Meta ETL (`meta_extractor`)

Rivery-style pipeline: **extract** (Meta Graph API) → **transform** (normalize) → **load** (DB). Used by `run-meta-etl`; config and field lists in `meta_extractor/config.py`.

## Optional: ngrok

```sh
ngrok http --url=clumplike-oswaldo-dowily.ngrok-free.dev 5005
```

Set `META_ADS_REDIRECT_URI` and Meta app callback URL to your ngrok URL (e.g. `https://your-subdomain.ngrok-free.dev/v1/campaign-ads/meta/auth/callback`).
