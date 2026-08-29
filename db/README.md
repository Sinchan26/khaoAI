# khaoAI Database Migrations

This folder contains Alembic migrations for PostgreSQL.

## How to run migrations manually

Ensure PostgreSQL is running and the database exists:

```bash
createdb khaoai
```

### Apply all migrations
```bash
alembic upgrade head
```

### Environment Variable
In your `.env` or `local.settings.json`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/khaoai
```
