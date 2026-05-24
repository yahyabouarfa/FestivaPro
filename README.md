# FestivaPro

Full-stack festival bar management app for event-night bar operations, stock control, staffing, analytics, and downloadable PDF/Excel reporting.

## Quick Start With Docker

```powershell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
docker compose up --build
```

Local URLs:

- Frontend: `http://127.0.0.1:5173`
- API: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- phpMyAdmin: `http://127.0.0.1:8080`

Seeded admin login:

```text
Email: admin@festivapro.local
Password: password
```

## Manual Setup

Create the MySQL database:

```sql
CREATE DATABASE festivapro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python seed.py
python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

## API Summary

- Auth: `/api/auth/login`, `/api/auth/refresh`, `/api/auth/me`, `/api/auth/logout`
- Admin CRUD: `/api/admin/events`, `/api/admin/bars`, `/api/admin/products`, `/api/admin/event-stock`, `/api/admin/stock`, `/api/admin/assignments`
- Analytics: `/api/admin/reports/summary`, `/api/admin/reports/event-insights`, `/api/admin/reports/event-comparison`, `/api/admin/reports/low-stock`
- Downloads: `/api/admin/reports/bar/{bar_id}/{pdf|xlsx}`, `/api/admin/reports/event/{event_id}/bars/{pdf|xlsx}`, `/api/admin/reports/event/{event_id}/full/{pdf|xlsx}`, `/api/admin/reports/event/{event_id}/bundle`
- Employee: `/api/employee/dashboard`, `/api/employee/contribution`

## Role Matrix

| Feature | Admin | Bartender |
| --- | --- | --- |
| Manage events, bars, stock, prices | Yes | No |
| Random staff assignment | Yes | No |
| Financial analytics and P&L | Yes | No |
| Download PDF/XLSX/ZIP reports | Yes | No |
| See assigned bar and product prices | No | Yes |
| See own contribution metrics | No | Yes |
| See all financial data | Yes | No |
| Audit log visibility | Yes | No |

## Differentiators Beyond Excel

- Real-time multi-user web access through the FastAPI backend and React frontend.
- Role-based data visibility: bartenders only see assigned bar, products, and their own contribution data.
- One-click random staff assignment across multiple bars.
- Low-stock alert endpoint and dashboard warning state.
- Cross-event analytics for profit, revenue, product performance, and staff performance.
- Audit log for price changes, assignments, and stock edits.
- One-click ZIP report bundle for full event reporting.

The versioned schema lives in `backend/alembic/versions/202605240001_initial_schema.py`. A phpMyAdmin-friendly SQL copy is in `migrations/001_initial_schema.sql`.
