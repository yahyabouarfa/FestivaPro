# FESTIVAPRO EVENT MANAGEMENT

Professional SaaS platform for Moroccan nightlife festivals and premium event operations.

## Stack

- Frontend: React, Vite, TailwindCSS, Framer Motion, React Query, Axios
- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic, JWT
- Database: MySQL with phpMyAdmin
- Deployment: Docker Compose with an nginx-served frontend
- CI/CD: GitHub Actions

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Services:

- Web app: http://localhost:8080
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- phpMyAdmin: http://localhost:8081

Default admin is configured through `.env`:

- `DEFAULT_ADMIN_EMAIL`
- `DEFAULT_ADMIN_PASSWORD`

## Theme System

The official `FestivaPro.png` logo lives in the repository root. The frontend copies it into `frontend/public` before `dev` and `build`, samples its colors in the browser, and exposes the generated palette as CSS variables:

- `--color-primary`
- `--color-secondary`
- `--color-accent`
- `--gradient-neon`
- `--shadow-glow`

These variables power buttons, KPI cards, charts, shadows, and PDF/report color constants.

## Local Development

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## API Areas

- Authentication
- Events
- Bars
- Employees
- Stock
- Equipment and logistics
- Salaries
- Bartender contributions
- Profit entries
- Night management
- Reports
- Notifications
- Audit logs
- Dashboard analytics

## Git Workflow

Recommended branch flow:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/current-part-name
```

Before opening a PR into `develop`, run:

```bash
cd backend && pytest
cd ../frontend && npm run build
cd .. && docker compose up --build
```
