# FestivaPro

FestivaPro is a full-stack festival bar management application for event teams that run multiple bars across multiple nights. It helps an admin create events, open nights, assign employees, track stock, reconcile cash, calculate profit, generate PDF reports, and keep an audit trail.

The interface is currently in French and the business logic is designed around Moroccan festival operations using MAD as the currency.

## Stack

- Backend: Python, FastAPI, SQLAlchemy ORM
- Auth: JWT access tokens and refresh tokens
- Frontend: React, hooks, React Router, Axios
- Database: MySQL, with phpMyAdmin support
- Migrations: Alembic versions plus SQL copies in `migrations/`
- Reports: server-side PDF generation stored in the database

## Local URLs

Current development ports in this workspace:

| Service | URL |
| --- | --- |
| Frontend | `http://127.0.0.1:5176` |
| API | `http://127.0.0.1:8002` |
| API docs | `http://127.0.0.1:8002/docs` |
| phpMyAdmin | `http://127.0.0.1:8080` |

Docker defaults may use:

| Service | URL |
| --- | --- |
| Frontend | `http://127.0.0.1:5173` |
| API | `http://127.0.0.1:8000` |
| phpMyAdmin | `http://127.0.0.1:8080` |

## Demo Credentials

These credentials are also displayed on the login page.

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@festivapro.local` | `password` |
| Employee | `seed.yassine@festivapro.local` | `password` |

## User Roles

### Admin

Admins can manage the full operational workflow:

- Create events and planned nights.
- Add bars to events.
- Assign a responsible per bar for each night.
- Assign employees to a bar for a night.
- Randomly assign a chosen number of available employees to one bar.
- Enter opening stock by bar and product.
- Enter remaining stock at the end of the night.
- Enter cash collected per assigned employee.
- Close bars, nights, and full events.
- Download PDF reports.
- View audit logs, profit snapshots, stock data, and event reports.

### Employee

Employees have a read-only bartender dashboard:

- Active event and location.
- Their assigned bar for the active night.
- The night responsible for their bar.
- Their shift salary.
- Selling price list for their bar.
- Cash contribution after the admin records it.
- Contribution percentage after the bar is closed.

Employees cannot see other bars, other employees' financial data, or admin reports.

## Core Navigation

The admin workflow is a drill-down dashboard:

1. Events dashboard.
2. Single event screen.
3. Single night screen.
4. Bar panels inside the selected night.
5. Reports page for generated PDFs.

The root admin page after login is the events dashboard.

## Full Business Workflow

### 1. Create Event

Admin creates an event with:

- Event name.
- Moroccan city or location.
- Start date.
- Planned number of nights.
- Attendance count, when needed for reports.

Creating an event creates only the event record. Nights are started manually from inside the event.

### 2. Add Bars

Inside an event, admin adds bars such as:

- Bar VIP
- GOLD
- Bar Nord
- Main Bar

Bars are created with a name only. The responsible is assigned inside each night, because the responsible can change from one night to another.

Bars can be added while an event is upcoming or active. Closed events are read-only.

### 3. Begin Night

Admin starts a night from the event screen by selecting the night date.

Rules:

- Only one night can be active at a time.
- A new night cannot begin until the previous night is closed.
- No new night can be added to a closed event.
- The event cannot exceed its planned number of nights.

For night 2 and later, opening stock is carried forward from the previous night's closing stock.

### 4. Assign Staff

Inside a night, admin assigns staff per bar.

Manual assignment:

- Select a bar.
- Select the responsible for that night.
- Enter the salary for that night.

Random assignment:

- Select a bar.
- Enter how many employees should be assigned.
- Enter the salary per employee.
- The system only uses employees not already assigned to another bar in the same night.

Assignments are stored per night, per bar, per employee.

### 5. Opening Stock

Before the night runs, admin enters opening stock per bar:

- Bar.
- Product.
- Quantity.
- Selling price.

The system automatically creates or updates the event stock pool when needed. If the same product is added again to the same bar and night, the quantity is added to the existing row instead of creating a duplicate.

### 6. End Of Night

End-of-night data is split into two focused forms.

Stock form:

- Bar.
- Product.
- Remaining quantity.

After selecting a bar, the product dropdown only shows products that were opened for that bar in that night.

Cash form:

- Bar.
- Employee.
- Cash collected.

After selecting a bar, the employee dropdown only shows employees assigned to that bar in that night.

Close bar:

- Locks the bar after all stock and cash entries are complete.
- Prevents future edits for that bar and night.

### 7. Cash Reconciliation

For each bar, the system calculates:

- Quantity used = opening quantity + top-up - remaining quantity.
- Expected cash = quantity used * selling price.
- Actual cash = sum of cash collected from assigned employees.
- Cash discrepancy = expected cash - actual cash.

Discrepancy labels:

- Balanced: discrepancy is zero.
- Missing: expected cash is higher than collected cash.
- Surplus: collected cash is higher than expected cash.

### 8. Profit Calculation

Per bar/night:

- Total cash collected.
- Expected cash.
- Cash discrepancy.
- Stock cost.
- Staff cost.
- Gross profit.
- Net profit.
- Expected profit.

Per event:

- Total revenue.
- Total stock cost.
- Total staff cost.
- Total net profit.
- Event-level profit snapshots.

Dashboards and reports load from stored snapshots and summaries rather than recalculating everything on every page load.

### 9. Close Night

A night can be closed only after every bar in that night is closed.

On close night:

- The night status becomes closed.
- Bar stock rows are locked.
- Profit snapshots are written.
- Bar/night PDF reports are generated.
- Full night PDF report is generated.
- Carryover opening stock is prepared for the next night when applicable.

### 10. Close Event

An event can be closed only when all planned nights are closed.

On close event:

- Event status becomes closed.
- Full event PDF report is generated.
- Event becomes read-only.
- No bars, nights, stock, cash, assignments, or summaries can be changed.

## Main Database Tables

Core users and auth:

- `users`
- `refresh_tokens`

Events and structure:

- `events`
- `event_nights`
- `bars`
- `bar_assignments`

Products and stock:

- `product_categories`
- `products`
- `event_stock`
- `bar_night_stock`
- `price_history`

Staff and cash:

- `night_bar_assignments`
- `event_salaries`
- `bartender_cash`
- `bartender_sales`

Summaries and reporting:

- `bar_night_summary`
- `profit_snapshots`
- `pdf_reports`
- `audit_logs`

## Reports

Reports are generated server-side and stored in `pdf_reports`.

Report types:

- Bar/night report.
- Full night report.
- Full event report.

Reports include:

- Event, night, bar, date, and location.
- Staff and salaries.
- Cash collected by employee.
- Stock opening, top-up, closing, and used quantity.
- Expected cash and actual cash.
- Cash discrepancy.
- Stock cost.
- Staff cost.
- Gross profit.
- Net profit.
- Blank signature lines for physical review.

Reports remain downloadable after an event is closed.

## Audit Log

Important actions write to `audit_logs`, including:

- Event creation.
- Night opening.
- Bar creation.
- Stock entry.
- Cash entry.
- Bar close.
- Night close.
- Event close.
- Seed actions.
- Bulk maintenance actions.

Each log stores:

- User ID.
- Action.
- Entity type.
- Entity ID.
- Details.
- Timestamp.

## Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python -m app.scripts.seed_past_events
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

Important backend variables:

```env
DATABASE_URL=mysql+pymysql://festivapro_user:festivapro_password@127.0.0.1:3306/festivapro
CORS_ORIGINS=http://localhost:5176,http://127.0.0.1:5176
SECRET_KEY=change-this-to-a-long-random-secret
```

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5176
```

Frontend API variable:

```env
VITE_API_URL=http://127.0.0.1:8002/api
```

## Docker Setup

```powershell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
docker compose up --build
```

Useful Docker services:

- `db`: MySQL 8.4.
- `backend`: FastAPI app.
- `frontend`: React/Vite app.
- `phpmyadmin`: MySQL admin UI.

If migrations or seed data are not run automatically:

```powershell
cd backend
alembic upgrade head
python -m app.scripts.seed_past_events
```

## phpMyAdmin

Open:

```text
http://127.0.0.1:8080
```

Default database values from Docker:

| Setting | Value |
| --- | --- |
| Database | `festivapro` |
| User | `festivapro_user` |
| Password | `festivapro_password` |
| Root password | `root_password` |

## Seed Data

Run:

```powershell
cd backend
python -m app.scripts.seed_past_events
```

The seed script creates complete closed historical events with:

- Events.
- Nights.
- Bars.
- Products and categories.
- Event stock.
- Night assignments.
- Salaries.
- Opening and closing stock.
- Cash collection.
- Bar summaries.
- Profit snapshots.
- Price history.
- Audit logs.
- PDF reports.

Seeded historical events include:

- `Mawazine Lounge 2025`
- `Casa Beach Festival 2025`
- `Atlas Night Market 2024`

## API Overview

Authentication:

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `POST /api/auth/logout`

Admin resources:

- `/api/admin/events`
- `/api/admin/event-nights`
- `/api/admin/bars`
- `/api/admin/product-categories`
- `/api/admin/products`
- `/api/admin/event-stock`
- `/api/admin/night-assignments`
- `/api/admin/opening-stock`
- `/api/admin/end-of-night`
- `/api/admin/bar-night-summaries`
- `/api/admin/profit-snapshots`
- `/api/admin/pdf-reports`
- `/api/admin/audit-logs`

Employee:

- `GET /api/employee/dashboard`
- `GET /api/employee/contribution`

Analytics:

- `/api/admin/reports/summary`
- `/api/admin/reports/bar-financials`
- `/api/admin/reports/best-sellers`
- `/api/admin/reports/low-stock`
- `/api/admin/reports/waste`
- `/api/admin/reports/bartender-leaderboard`
- `/api/admin/reports/event-insights`
- `/api/admin/reports/event-comparison`

## Migrations

Alembic migrations:

```text
backend/alembic/versions/
```

SQL migration copies:

```text
migrations/
```

Apply migrations:

```powershell
cd backend
alembic upgrade head
```

## Verification

Backend syntax check:

```powershell
python -m compileall backend\app
```

Frontend build:

```powershell
cd frontend
npm run build
```

Health checks:

```powershell
Invoke-WebRequest http://127.0.0.1:8002/docs
Invoke-WebRequest http://127.0.0.1:5176
```

## Operational Rules

- Closed events are read-only.
- Closed nights cannot be edited.
- Closed bars cannot receive stock or cash edits.
- A new night cannot start before the previous one is closed.
- A night cannot close until all bars are closed.
- An event cannot close until all planned nights are closed.
- Random bar assignment excludes employees already assigned elsewhere in that same night.
- End-of-night stock shows only products opened for the selected bar.
- End-of-night cash shows only employees assigned to the selected bar.
- PDF reports remain downloadable after closing.

## Notes For Developers

- Prefer using the official close flows instead of manually setting statuses in the database.
- Use stored `bar_night_summary` and `profit_snapshots` for dashboard and report data.
- Keep migration scripts version-controlled when changing schema.
- The frontend has route-level protection and the backend enforces role access.
- Backend errors return clear validation messages for forbidden workflow transitions.
