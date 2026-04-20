"""Add Audit Vault fields to ChatMessage

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-11 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to chat_messages table
    op.add_column('chat_messages', sa.Column('metadata_snapshot', sa.JSON(), nullable=True))
    op.add_column('chat_messages', sa.Column('audit_log_snapshot', sa.JSON(), nullable=True))
    op.add_column('chat_messages', sa.Column('action_metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove columns from chat_messages table
    op.drop_column('chat_messages', 'action_metadata')
    op.drop_column('chat_messages', 'audit_log_snapshot')
    op.drop_column('chat_messages', 'metadata_snapshot')
