"""add email_logs

Registro de tentativas de e-mail automático (2.1.0-rc.1). Migration idempotente:
só cria a tabela se ela ainda não existir.

Revision ID: b7d2f4a91c33
Revises: 9c4e1a7b2d10
Create Date: 2026-10-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d2f4a91c33"
down_revision: Union[str, Sequence[str], None] = "9c4e1a7b2d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "email_logs" in inspector.get_table_names():
        return
    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("destinatario", sa.String(length=255), nullable=False),
        sa.Column("template", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("detalhe", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_logs_id"), "email_logs", ["id"], unique=False)
    op.create_index(op.f("ix_email_logs_lead_id"), "email_logs", ["lead_id"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "email_logs" in inspector.get_table_names():
        op.drop_index(op.f("ix_email_logs_lead_id"), table_name="email_logs")
        op.drop_index(op.f("ix_email_logs_id"), table_name="email_logs")
        op.drop_table("email_logs")
