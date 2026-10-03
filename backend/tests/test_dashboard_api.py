import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.auth import get_current_user
from src.database import Base
from src.dependencies import get_db
from src.core.exceptions import ConflictError
from src.main import app
from src.models.product import Product
from src.models.transaction import Transaction, TransactionStatus, TransactionType
from src.schemas.transaction import TransactionCreate
from src.services.transaction_service import create_transaction, delete_transaction

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = lambda: {"sub": "anonymous"}


def setup_function() -> None:
    Base.metadata.create_all(bind=engine)


def teardown_function() -> None:
    Base.metadata.drop_all(bind=engine)


def test_sale_and_purchase_adjust_inventory_and_dashboard_totals() -> None:
    with Session(bind=engine) as db:
        product = Product(
            name="Rice",
            category="Grains",
            price=Decimal("25.00"),
            cost=Decimal("12.00"),
            stock=10,
            unit="kg",
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        product_id = product.id

    client = TestClient(app)
    purchase_response = client.post(
        "/api/transactions",
        json={"type": "purchase", "item": "Rice", "quantity": 5, "total": "125.00", "counterparty": "Supplier", "status": "paid", "product_id": str(product_id)},
    )
    assert purchase_response.status_code == 201
    with Session(bind=engine) as db:
        product = db.get(Product, product_id)
        db.refresh(product)
        assert product.stock == 15

    sale_response = client.post(
        "/api/transactions",
        json={"type": "sale", "item": "Rice", "quantity": 3, "total": "75.00", "counterparty": "Customer", "status": "paid", "product_id": str(product_id)},
    )
    assert sale_response.status_code == 201
    with Session(bind=engine) as db:
        product = db.get(Product, product_id)
        assert product.stock == 12

    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    payload = response.json()
    assert payload["revenue"] == "75.00"
    assert payload["total_purchases"] == "125.00"
    assert payload["expenses"] == "0"
    assert payload["net_cash_flow"] == "-50.00"
    assert payload["low_stock_count"] == 0


def test_transaction_service_adjusts_and_restores_linked_product_stock() -> None:
    with Session(bind=engine) as db:
        product = Product(
            name="Rice",
            category="Grains",
            price=Decimal("25.00"),
            cost=Decimal("12.00"),
            stock=10,
            unit="kg",
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        sale = create_transaction(
            db,
            TransactionCreate(type=TransactionType.SALE, item="Rice", quantity=3, total=Decimal("75.00"), product_id=product.id),
        )
        db.refresh(product)
        assert product.stock == 7

        purchase = create_transaction(
            db,
            TransactionCreate(type=TransactionType.PURCHASE, item="Rice", quantity=5, total=Decimal("125.00"), product_id=product.id),
        )
        db.refresh(product)
        assert product.stock == 12

        delete_transaction(db, purchase.id)
        db.refresh(product)
        assert product.stock == 7


def test_transaction_service_rejects_unlinked_stock_transactions() -> None:
    with Session(bind=engine) as db:
        for transaction_type in (TransactionType.SALE, TransactionType.PURCHASE):
            try:
                create_transaction(
                    db,
                    TransactionCreate(type=transaction_type, item="Rice", quantity=1, total=Decimal("25.00")),
                )
            except ConflictError:
                continue
            raise AssertionError(f"{transaction_type.value} without a product should be rejected")


def test_low_stock_detection_counts_under_threshold_products() -> None:
    with Session(bind=engine) as db:
        low_stock = Product(
            name="Beans",
            category="Grains",
            price=Decimal("18.00"),
            cost=Decimal("10.00"),
            stock=4,
            unit="kg",
        )
        healthy = Product(
            name="Yam",
            category="Tubers",
            price=Decimal("30.00"),
            cost=Decimal("18.00"),
            stock=20,
            unit="kg",
        )
        db.add_all([low_stock, healthy])
        db.commit()

    client = TestClient(app)
    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    payload = response.json()
    assert payload["low_stock_count"] == 1


def test_assistant_answers_from_backend_owned_facts() -> None:
    with Session(bind=engine) as db:
        product = Product(
            name="Rice",
            category="Grains",
            price=Decimal("25.00"),
            cost=Decimal("12.00"),
            stock=3,
            unit="kg",
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        now = datetime.now(timezone.utc)
        db.add_all(
            [
                Transaction(type=TransactionType.SALE, item="Rice", quantity=4, total=Decimal("100.00"), created_at=now, product_id=product.id),
                Transaction(type=TransactionType.PURCHASE, item="Rice", quantity=2, total=Decimal("40.00"), created_at=now),
                Transaction(type=TransactionType.EXPENSE, item="Transport", quantity=1, total=Decimal("10.00"), created_at=now),
                Transaction(type=TransactionType.SALE, item="Rice", quantity=99, total=Decimal("990.00"), created_at=now - timedelta(days=10), product_id=product.id),
            ]
        )
        db.commit()

    client = TestClient(app)
    questions = {
        "How much did I make today?": ("daily_earnings", "100.00"),
        "What did I spend this week?": ("weekly_spend", "50.00"),
        "What's my best-selling product?": ("best_selling", "103"),
        "What should I restock?": ("restock", "Rice"),
    }
    for question, (intent, expected) in questions.items():
        response = client.post("/api/assistant/answer", json={"question": question})
        assert response.status_code == 200
        payload = response.json()
        assert payload["intent"] == intent
        assert expected in response.text
