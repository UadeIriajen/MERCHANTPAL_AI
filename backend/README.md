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
    services/       Business logic that spans repositories:
                       transcript_parser.py   the "AI" step (see below)
                       transaction_service.py create/delete + stock side effects
    routers/        HTTP endpoints, one file per resource
  migrations/       Alembic migration environment
  alembic.ini
  requirements.txt
  .env.example
```

## The Voice → AI → Transaction → Database pipeline

```
POST /api/assistant/interpret   { transcript }        -> draft transaction (nothing saved)
       ↓ merchant reviews/edits the draft (Clarify screen)
POST /api/transactions          { ...draft, confirmed} -> saved, stock adjusted, dashboard updated
```

This two-step shape matches the frontend's existing Assistant → Clarify →
Confirm flow: the AI step never writes to the database by itself — it hands
back a draft for a human to confirm, same as `Clarify` already does in the
UI.

**The "AI" step** has two implementations behind the same contract
(`str in -> ParsedTransaction out`), and `/assistant/interpret` uses
whichever is available:

- `src/services/llm_transcript_parser.py` — real understanding via Claude
  (`claude-opus-5`, structured outputs). Used automatically whenever
  `ANTHROPIC_API_KEY` is set (see `.env.example`). Handles free-form
  phrasing, not just the fixed sentence shapes below.
- `src/services/transcript_parser.py` — a dependency-free, rule-based
  fallback. No API key, works offline. Understands sentences shaped like
  *"\<verb\> [\<qty\> \<unit\> of] \<item\> to/from \<Name\> for \<amount\>"*
  — e.g. exactly the example already in the frontend's Clarify screen.

If the API key is missing, invalid, or the request fails for any reason
(rate limit, network), `llm_transcript_parser.py` catches it and falls back
to the rule-based parser — `/assistant/interpret` never hard-fails because
of this.

**Real audio capture doesn't exist yet on either side.** `/assistant/
interpret` takes a `transcript` string; the frontend's `VoiceRecording`
screen is a UI mock with no microphone access. Once you pick a
speech-to-text provider (e.g. Whisper), add an audio-upload variant of this
endpoint that transcribes first and feeds the result into the same
`parse_transcript_with_llm`/`parse_transcript` call — nothing else in the
pipeline changes.

## Transaction types: sales, purchases, expenses

One `transactions` table with a `type` column (`sale` | `purchase` |
`expense`) instead of three near-identical tables — they only differ in
which way money/stock moves:

| Type       | Stock effect (if `product_id` set) | Typical `counterparty` |
|------------|-------------------------------------|--------------------------|
| `sale`     | stock -= quantity                   | customer                |
| `purchase` | stock += quantity                   | supplier                 |
| `expense`  | none                                 | n/a                       |

Stock adjustment happens in `services/transaction_service.py`, not in the
router or repository — `create_transaction` applies it, `delete_transaction`
reverses it. **`PATCH` does not re-adjust stock** even if quantity/type/
product_id changes — void (delete) and recreate the transaction if the
stock effect needs to change.

## Endpoints implemented

| Method | Path                          | Purpose                                      |
|--------|--------------------------------|-----------------------------------------------|
| POST   | /api/assistant/interpret       | Voice transcript → AI → draft transaction     |
| POST   | /api/transactions              | Create transaction (sale/purchase/expense)    |
| GET    | /api/transactions              | Get transactions — filter with `?type=` / `?status=` |
| GET    | /api/transactions/{id}         | Get one transaction                            |
| PATCH  | /api/transactions/{id}         | Update transaction                             |
| DELETE | /api/transactions/{id}         | Delete transaction (reverses stock effect)     |
| GET    | /api/inventory                 | Get inventory (list)                           |
| GET    | /api/inventory/{id}            | Get one inventory item                          |
| PATCH  | /api/inventory/{id}             | Update inventory                                |
| GET    | /api/dashboard/stats           | Get dashboard statistics                        |
| GET    | /api/healthz                   | Health check                                     |

`GET /api/dashboard/stats` returns `total_sales`, `total_purchases`,
`total_expenses`, `net_cash_flow` (sales − purchases − expenses),
`total_transactions`, `inventory_value`, `low_stock_count` — each computed
by real SQL aggregation, not hardcoded.

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

## Supabase setup

1. In Supabase Dashboard, open **Project Settings -> API** and copy the
  **Project URL** and **anon public key**.
2. Put the Project URL and anon key in both `FRONTEND/.env` as
  `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`, and `backend/.env` as
  `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
3. Run `alembic upgrade head` from `backend/` to add the `owner_id` columns.
4. Restart the frontend and backend.

When `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set, all business APIs require
the Supabase bearer token and scope products, transactions, analytics, assistant
answers, and notifications to the signed-in user. `SUPABASE_JWT_SECRET` is only
needed for legacy HS256 projects; modern projects can leave it empty.

The public anon key is safe to use in the browser. Never put a Supabase
`service_role` key in frontend files or commit it to the repository.

Then visit `http://localhost:8000/docs` for interactive Swagger UI.

## Notes

- `Base.metadata.create_all()` runs on startup so the API is queryable
  immediately in dev without running Alembic first. Once you have real data
  you care about, switch to `alembic upgrade head` as the source of truth
  and drop the `create_all` call in `main.py`.
- `DATABASE_URL` is required (no silent SQLite fallback) — same behavior as
  `lib/db/src/index.ts` on the TypeScript side, so both stacks fail loudly
  instead of quietly writing to the wrong database.
- Money fields serialize as strings (e.g. `"5000.00"`) since they're
  `Decimal` under the hood — the frontend needs `Number(...)` before doing
  math or formatting.
