# FestivaPro

Full-stack festival bar management app.

## Local URLs

- Frontend: `http://127.0.0.1:5174`
- API: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`

## Database

Create the MySQL database in phpMyAdmin:

```sql
CREATE DATABASE festivapro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Copy `backend/.env.example` to `backend/.env`, update `DATABASE_URL`, then run. The initial migration creates the full event/bar/product/stock schema and seeds demo data:

```powershell
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Seeded admin login:

```text
Email: admin@festivapro.local
Password: password
```

The versioned schema lives in `backend/alembic/versions/202605240001_initial_schema.py`. A phpMyAdmin-friendly SQL copy is in `migrations/001_initial_schema.sql`.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```
