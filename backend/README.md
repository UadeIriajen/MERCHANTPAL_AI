# MerchantPal backend (FastAPI)

A standalone Python service — separate from the `pnpm` workspace that
`FRONTEND` and `lib/*` live in. It talks Postgres via SQLAlchemy and can
point at the same database `lib/db` (Drizzle) is configured for.

## Layout

```
backend/
  src/
    main.py         FastAPI app: CORS, routers, startup table creation, /api/healthz
    config.py       Settings loaded from .env (DATABASE_URL, CORS_ORIGINS)
    database.py     SQLAlchemy engine/session + declarative Base
    dependencies.py FastAPI Depends (get_db)
    core/           Cross-cutting bits (custom exceptions + handlers)
    models/         SQLAlchemy ORM tables (Product, Transaction)
    schemas/        Pydantic request/response models
    repository/     DB access per table, plus dashboard aggregate queries
    routers/        HTTP endpoints, one file per resource
  migrations/       Alembic migration environment
  alembic.ini
  requirements.txt
  .env.example
```

## Endpoints implemented

| Method | Path                     | Purpose                  |
|--------|--------------------------|---------------------------|
| POST   | /api/transactions        | Create transaction        |
| GET    | /api/transactions        | List transactions         |
| GET    | /api/transactions/{id}   | Get one transaction       |
| PATCH  | /api/transactions/{id}   | Update transaction        |
| DELETE | /api/transactions/{id}   | Delete transaction        |
| GET    | /api/inventory           | Get inventory (list)      |
| GET    | /api/inventory/{id}      | Get one inventory item    |
| PATCH  | /api/inventory/{id}      | Update inventory          |
| GET    | /api/dashboard/stats     | Get dashboard statistics  |
| GET    | /api/healthz             | Health check               |

> Note: the frontend's Inventory screen also does create + delete for
> products (`AddProduct`, the trash icon in `Inventory`). Those two
> endpoints weren't in the original list — say the word and they're a
> straightforward addition to `routers/inventory.py` + `repository/product_repository.py`.

## Local setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with a real DATABASE_URL

# create the tables (dev-quick way; startup also does this automatically)
alembic revision --autogenerate -m "init"
alembic upgrade head

uvicorn src.main:app --reload --port 8000
```

Then visit `http://localhost:8000/docs` for interactive Swagger UI.

## Notes

- `Base.metadata.create_all()` runs on startup so the API is queryable
  immediately in dev without running Alembic first. Once you have real data
  you care about, switch to `alembic upgrade head` as the source of truth
  and drop the `create_all` call in `main.py`.
- `DATABASE_URL` is required (no silent SQLite fallback) — same behavior as
  `lib/db/src/index.ts` on the TypeScript side, so both stacks fail loudly
  instead of quietly writing to the wrong database.
