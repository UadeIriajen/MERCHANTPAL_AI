"""Add Supabase owner IDs to business records.

Revision ID: 20260905_owner_id
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "20260905_owner_id"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False, server_default="Merchant"),
        sa.Column("business", sa.String(length=200), nullable=False, server_default="My business"),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="other"),
        sa.Column("description", sa.String(length=1000), nullable=False, server_default=""),
    )
    op.add_column("products", sa.Column("owner_id", sa.String(length=64), nullable=True))
    op.create_index("ix_products_owner_id", "products", ["owner_id"])
    op.add_column("transactions", sa.Column("owner_id", sa.String(length=64), nullable=True))
    op.create_index("ix_transactions_owner_id", "transactions", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_transactions_owner_id", table_name="transactions")
    op.drop_column("transactions", "owner_id")
    op.drop_index("ix_products_owner_id", table_name="products")
    op.drop_column("products", "owner_id")
    op.drop_table("profiles")
