# FastAPI MySQL Example

This project demonstrates a simple CRUD API using FastAPI, SQLAlchemy and MySQL, plus campaign-ads endpoints compatible with the nyx-api shape.

## Setup

1. **Python version:** Use **Python 3.11 or 3.12**. If you see a `pydantic-core` / `ForwardRef._evaluate()` error when installing, you're likely on Python 3.14; create the venv with an older interpreter:
   ```sh
   python3.12 -m venv venv    # or python3.11
   ```

2. Create a virtual environment and install requirements:
   ```sh
   cd fastapi-mysql
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure your MySQL connection (optional; default uses `meta_poc`):
   ```sh
   export DATABASE_URL="mysql+mysqlconnector://root:biswa123@localhost:3306/meta_poc"
   ```

## Run MySQL and server

1. **Start MySQL** (if not already running):

   - **macOS (Homebrew):**
     ```sh
     brew services start mysql
     ```
   - **macOS (MySQL .dmg):** Open **System Preferences → MySQL → Start MySQL Server**, or:
     ```sh
     sudo /usr/local/mysql/support-files/mysql.server start
     ```
   - **Linux (systemd):**
     ```sh
     sudo systemctl start mysql
     ```
   - **Windows:** Start **Services** → find **MySQL** → Start, or:
     ```sh
     net start MySQL
     ```

2. **Create the database** (once):
   ```sh
   mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS meta_poc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
   ```
   Or run `scripts/init_meta_poc.sql`.

3. **Start the FastAPI server** (tables `user` and `integration` are created on first run):

   **Option A – from project directory:**
   ```sh
   cd fastapi-mysql
   source venv/bin/activate
   uvicorn main:app --reload --host 0.0.0.0 --port 5005
   ```

   **Option B – from anywhere (avoids "Could not import module main"):**
   ```sh
   cd fastapi-mysql
   source venv/bin/activate
   python run.py
   ```

   API base: **http://localhost:5005**

## Campaign-ads API (v1)

- **GET** `/v1/campaign-ads/status/{workspace_id}` – List integrations for a workspace (no auth for POC).
- **POST** `/v1/campaign-ads/meta/auth` – Get Meta OAuth URL. Body: `{"workspace_id": 2, "brand_id": 1}`. Optional env: `META_ADS_CLIENT_ID`, `META_ADS_REDIRECT_URI`.
- **POST** `/v1/campaign-ads/revoke-access` – Revoke integration. Body: `{"workspace_id": 22, "tokenRecord_id": 87}`.