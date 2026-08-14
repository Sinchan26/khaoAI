# khaoAI Database Migrations

This folder contains database migration scripts for PostgreSQL.

## How to run migrations manually

Ensure PostgreSQL is running and your database is created:

```bash
createdb khaoai
```

### Apply Migration 001
```bash
psql -U postgres -d khaoai -f migrations/001_init.sql
```

### Environment Variable
In your `.env` or `local.settings.json`:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/khaoai
```
