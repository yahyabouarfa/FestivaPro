# Contributing

## Branches

- `main`: production-ready releases
- `develop`: integration branch
- `feature/*`: scoped work branches

## Workflow

1. Checkout `develop`.
2. Pull the latest changes.
3. Create a feature branch.
4. Run backend tests, frontend build, and Docker Compose before pushing.
5. Open a pull request into `develop`.

## Quality Bar

- No frontend-only fake data.
- API changes need schema and migration updates when persistence changes.
- UI must remain responsive on desktop, laptop, tablet, and mobile.
- Authentication-protected routes must use JWT.
- Audit-sensitive mutations should record audit logs.
