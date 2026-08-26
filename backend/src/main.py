from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.core.exceptions import NotFoundError, not_found_handler
from src.database import Base, engine
from src.routers import dashboard, inventory, transactions

settings = get_settings()

app = FastAPI(title="MerchantPal API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(NotFoundError, not_found_handler)

app.include_router(transactions.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    # Convenience for local dev so the API is queryable immediately. For
    # anything beyond local dev, manage schema changes with Alembic instead
    # (see backend/migrations) and drop this call.
    Base.metadata.create_all(bind=engine)


@app.get("/api/healthz")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
