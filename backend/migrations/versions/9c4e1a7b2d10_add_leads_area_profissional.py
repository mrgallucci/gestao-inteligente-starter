"""add leads.area_profissional

A coluna `area_profissional` existe no model `Lead` (e é usada pelo endpoint
público de e-book e pelas telas do CRM), mas não estava na migration inicial.
Em uma instalação limpa, `alembic upgrade head` criava `leads` sem a coluna e
qualquer consulta a Leads falhava.

A migration é idempotente: bancos recuperados com `legacy_upgrade.py` ou
ajustados manualmente podem já possuir a coluna.

Revision ID: 9c4e1a7b2d10
Revises: 387ce60e2db5
Create Date: 2026-10-09 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c4e1a7b2d10"
down_revision: Union[str, Sequence[str], None] = "387ce60e2db5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _lead_columns() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns("leads")}


def upgrade() -> None:
    """Upgrade schema."""
    if "area_profissional" not in _lead_columns():
        op.add_column(
            "leads",
            sa.Column("area_profissional", sa.String(length=120), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    if "area_profissional" in _lead_columns():
        with op.batch_alter_table("leads") as batch_op:
            batch_op.drop_column("area_profissional")
