"""first migration that creates the items table"""
import sqlalchemy as sa
from alembic import op

# the id of this migration and the one before it
# there is no migration before this one
revision = "0001_create_items"
down_revision = None
branch_labels = None
depends_on = None


# build the items table and its columns
def upgrade():
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=30), nullable=False, server_default="OTHER"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="LOST"),
        sa.Column("location", sa.String(length=120), nullable=False),
        sa.Column("reporter_name", sa.String(length=100), nullable=False),
        sa.Column("contact", sa.String(length=120), nullable=False),
        sa.Column("claimed_by", sa.String(length=100), nullable=True),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    # an index on status makes filtering by status fast
    op.create_index("ix_items_status", "items", ["status"])


# undo the upgrade by removing the index and the table
def downgrade():
    op.drop_index("ix_items_status", table_name="items")
    op.drop_table("items")
