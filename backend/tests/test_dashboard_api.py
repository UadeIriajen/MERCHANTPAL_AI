import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base
from src.dependencies import get_db
from src.main import app
from src.models.product import Product
from src.models.transaction import Transaction, TransactionStatus, TransactionType

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


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

        purchase = Transaction(
            type=TransactionType.PURCHASE,
            item="Rice",
            quantity=5,
            total=Decimal("125.00"),
            counterparty="Supplier",
            status=TransactionStatus.PAID,
            product_id=product.id,
        )
        db.add(purchase)
        db.commit()
        db.refresh(product)

        sale = Transaction(
            type=TransactionType.SALE,
            item="Rice",
            quantity=3,
            total=Decimal("75.00"),
            counterparty="Customer",
            status=TransactionStatus.PAID,
            product_id=product.id,
        )
        db.add(sale)
        db.commit()
        db.refresh(product)

        assert product.stock == 12

    client = TestClient(app)
    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    payload = response.json()
    assert payload["revenue"] == "75.00"
    assert payload["expenses"] == "125.00"
    assert payload["profit"] == "-50.00"
    assert payload["low_stock_count"] == 0


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
        "What's my best-selling product?": ("best_selling", "4"),
        "What should I restock?": ("restock", "Rice"),
    }
    for question, (intent, expected) in questions.items():
        response = client.post("/api/assistant/answer", json={"question": question})
        assert response.status_code == 200
        payload = response.json()
        assert payload["intent"] == intent
        assert expected in response.text
