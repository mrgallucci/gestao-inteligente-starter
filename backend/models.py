from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# =========================================================
# CRM
# =========================================================


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    origem: Mapped[str] = mapped_column(String(100), nullable=False)
    objetivo: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Lead", nullable=False)
    interesse: Mapped[str] = mapped_column(String(50), nullable=False)
    contatos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Perfil B2C / analytics
    idade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    genero: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cidade: Mapped[str | None] = mapped_column(String(120), nullable=True)
    faixa_orcamento: Mapped[str | None] = mapped_column(String(80), nullable=True)

    # CRM SargLab / Workshop IA
    tipo_cliente: Mapped[str] = mapped_column(String(20), default="B2C", nullable=False)
    empresa: Mapped[str | None] = mapped_column(String(150), nullable=True)
    cargo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    area_profissional: Mapped[str | None] = mapped_column(String(120), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    consentimento_contato: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    segmento: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tamanho_equipe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dor_gatilho: Mapped[str | None] = mapped_column(Text, nullable=True)
    proxima_acao: Mapped[str | None] = mapped_column(Text, nullable=True)
    proxima_acao_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    motivo_perda: Mapped[str | None] = mapped_column(Text, nullable=True)
    formato_interesse: Mapped[str | None] = mapped_column(String(50), nullable=True)
    oferta_interesse: Mapped[str | None] = mapped_column(String(180), nullable=True)

    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    follow_up_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


# =========================================================
# MARKETING
# =========================================================


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    canal: Mapped[str] = mapped_column(String(80), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    custo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(180), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


# =========================================================
# PRODUTOS E VENDAS
# =========================================================


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantidade: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    forma_pagamento: Mapped[str] = mapped_column(String(50), nullable=False)
    status_pagamento: Mapped[str] = mapped_column(String(50), default="Pago", nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


# =========================================================
# LMS
# =========================================================


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


class CourseContent(Base):
    __tablename__ = "course_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    duracao_minutos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    url_conteudo: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("lead_id", "course_id", name="uq_enrollment_lead_course"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="Acesso liberado", nullable=False)
    acesso_liberado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    primeiro_acesso_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ultimo_acesso_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    concluido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


class ContentProgress(Base):
    __tablename__ = "content_progress"
    __table_args__ = (
        UniqueConstraint(
            "enrollment_id",
            "content_id",
            name="uq_content_progress_enrollment_content",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_id: Mapped[int] = mapped_column(
        ForeignKey("course_contents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    progresso: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    aberto_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ultima_atividade_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    concluido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)


# =========================================================
# USUÁRIOS / RBAC
# =========================================================


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="vendedor", nullable=False)
    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.id", ondelete="SET NULL"), unique=True, nullable=True, index=True
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ultimo_login_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
