"""Add ai_suggestions table for SOP editor actions

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_suggestions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.String(length=255), nullable=False),
        sa.Column("section_id", sa.String(length=255), nullable=False),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("section_type", sa.String(length=100), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("output_text", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("related_documents", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("audit_log_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("action_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_suggestions_action_type"), "ai_suggestions", ["action_type"], unique=False)
    op.create_index(op.f("ix_ai_suggestions_document_id"), "ai_suggestions", ["document_id"], unique=False)
    op.create_index(op.f("ix_ai_suggestions_section_id"), "ai_suggestions", ["section_id"], unique=False)
    op.create_index(op.f("ix_ai_suggestions_user_id"), "ai_suggestions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_suggestions_user_id"), table_name="ai_suggestions")
    op.drop_index(op.f("ix_ai_suggestions_section_id"), table_name="ai_suggestions")
    op.drop_index(op.f("ix_ai_suggestions_document_id"), table_name="ai_suggestions")
    op.drop_index(op.f("ix_ai_suggestions_action_type"), table_name="ai_suggestions")
    op.drop_table("ai_suggestions")
