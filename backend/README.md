# FestivaPro Backend

FastAPI REST API for festival bar management with SQLAlchemy, JWT access tokens, persisted refresh tokens, and MySQL migrations.

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Update `.env` with your MySQL credentials, then create the database in phpMyAdmin:

```sql
CREATE DATABASE festivapro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run migrations. The initial migration creates the full event/bar/product/stock schema and seeds demo data:

```powershell
alembic upgrade head
```

For phpMyAdmin-only setup, apply the SQL files in `../migrations/` in numeric order.

Seeded admin login:

```text
Email: admin@festivapro.local
Password: password
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

API docs are available at `http://127.0.0.1:8000/docs`.
