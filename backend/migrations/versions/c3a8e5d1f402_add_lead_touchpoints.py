"""add lead_touchpoints (atribuição de campanha por envio de formulário)

Guarda utm_source/medium/campaign/content/term, referrer e landing_url de cada
envio dos formulários públicos (e-book e contato do site). Migration idempotente:
só cria a tabela se ela ainda não existir. Não altera nenhuma tabela existente.

Revision ID: c3a8e5d1f402
Revises: b7d2f4a91c33
Create Date: 2026-10-13 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3a8e5d1f402"
down_revision: Union[str, Sequence[str], None] = "b7d2f4a91c33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "lead_touchpoints" in inspector.get_table_names():
        return
    op.create_table(
        "lead_touchpoints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("canal", sa.String(length=30), nullable=False),
        sa.Column("origem", sa.String(length=100), nullable=True),
        sa.Column("utm_source", sa.String(length=120), nullable=True),
        sa.Column("utm_medium", sa.String(length=120), nullable=True),
        sa.Column("utm_campaign", sa.String(length=180), nullable=True),
        sa.Column("utm_content", sa.String(length=180), nullable=True),
        sa.Column("utm_term", sa.String(length=180), nullable=True),
        sa.Column("referrer", sa.String(length=500), nullable=True),
        sa.Column("landing_url", sa.String(length=500), nullable=True),
        sa.Column("pagina", sa.String(length=200), nullable=True),
        sa.Column("consentimento_versao", sa.String(length=60), nullable=True),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_touchpoints_id"), "lead_touchpoints", ["id"], unique=False)
    op.create_index(op.f("ix_lead_touchpoints_lead_id"), "lead_touchpoints", ["lead_id"], unique=False)
    op.create_index(op.f("ix_lead_touchpoints_campaign_id"), "lead_touchpoints", ["campaign_id"], unique=False)
    op.create_index("ix_lead_touchpoints_utm", "lead_touchpoints", ["utm_source", "utm_medium", "utm_campaign"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "lead_touchpoints" in inspector.get_table_names():
        op.drop_index("ix_lead_touchpoints_utm", table_name="lead_touchpoints")
        op.drop_index(op.f("ix_lead_touchpoints_campaign_id"), table_name="lead_touchpoints")
        op.drop_index(op.f("ix_lead_touchpoints_lead_id"), table_name="lead_touchpoints")
        op.drop_index(op.f("ix_lead_touchpoints_id"), table_name="lead_touchpoints")
        op.drop_table("lead_touchpoints")
