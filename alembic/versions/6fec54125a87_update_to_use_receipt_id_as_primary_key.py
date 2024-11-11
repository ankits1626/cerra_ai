"""Update to use receipt_id as primary key

Revision ID: 6fec54125a87
Revises: 5f8497cad6bd
Create Date: 2024-11-05 07:59:31.507090

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "6fec54125a87"
down_revision = "5f8497cad6bd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the existing table
    op.drop_table("receipt_approver_responses")
    # Recreate the table with the new structure
    op.create_table(
        "receipt_approver_responses",
        sa.Column("receipt_id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("client", sa.String, nullable=False),
        sa.Column("ocr_raw", sa.JSON, nullable=False),
        sa.Column("processed", sa.JSON, nullable=False),
        sa.Column("user_input_data", sa.JSON, nullable=False),
        sa.Column("receipt_classifier_response", sa.JSON, nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    # Drop the recreated table
    op.drop_table("receipt_approver_responses")
