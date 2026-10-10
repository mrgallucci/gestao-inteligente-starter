"""Recuperação idempotente para bancos do Gestão Inteligente anteriores à reconstrução.

Use SOMENTE quando as tabelas antigas ainda existem e o histórico Alembic original foi
perdido. Faça backup do banco antes. Em instalação nova, use `alembic upgrade head`.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, inspect, text
from sqlalchemy.schema import CreateColumn

from database import engine
from models import Base

HEAD_REVISION = "387ce60e2db5"

LEAD_COLUMNS = [
    Column("idade", Integer, nullable=True),
    Column("genero", String(50), nullable=True),
    Column("cidade", String(120), nullable=True),
    Column("faixa_orcamento", String(80), nullable=True),
    Column("tipo_cliente", String(20), nullable=False, server_default=text("'B2C'")),
    Column("empresa", String(150), nullable=True),
    Column("cargo", String(120), nullable=True),
    Column("email", String(255), nullable=True),
    Column("area_profissional", String(120), nullable=True),
    Column("telefone", String(50), nullable=True),
    Column("consentimento_contato", Boolean, nullable=False, server_default=text("false")),
    Column("segmento", String(120), nullable=True),
    Column("tamanho_equipe", Integer, nullable=True),
    Column("dor_gatilho", Text, nullable=True),
    Column("proxima_acao", Text, nullable=True),
    Column("proxima_acao_em", DateTime, nullable=True),
    Column("motivo_perda", Text, nullable=True),
    Column("formato_interesse", String(50), nullable=True),
    Column("oferta_interesse", String(180), nullable=True),
    Column("campaign_id", Integer, nullable=True),
]

CAMPAIGN_COLUMNS = [
    Column("utm_source", String(120), nullable=True),
    Column("utm_medium", String(120), nullable=True),
    Column("utm_campaign", String(180), nullable=True),
]

CONTENT_COLUMNS = [
    Column("descricao", Text, nullable=True),
    Column("url_conteudo", Text, nullable=True),
]


def add_missing_columns(connection, table_name: str, columns: list[Column]) -> None:
    inspector = inspect(connection)
    if table_name not in inspector.get_table_names():
        return
    existing = {item["name"] for item in inspector.get_columns(table_name)}
    for column in columns:
        if column.name in existing:
            continue
        ddl = str(CreateColumn(column).compile(dialect=connection.dialect))
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))
        print(f"+ {table_name}.{column.name}")


def main() -> None:
    print("Iniciando recuperação do schema legado...")
    # Cria tabelas que não existiam. Não altera tabelas já presentes.
    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        add_missing_columns(connection, "leads", LEAD_COLUMNS)
        add_missing_columns(connection, "campaigns", CAMPAIGN_COLUMNS)
        add_missing_columns(connection, "course_contents", CONTENT_COLUMNS)

        # Normaliza etapas antigas para o pipeline atual do SargLab.
        connection.execute(text("UPDATE leads SET status='Lead' WHERE status='Novo'"))
        connection.execute(text("UPDATE leads SET status='Contato realizado' WHERE status='Contatado'"))
        connection.execute(text("UPDATE leads SET status='Interessado' WHERE status='Qualificado'"))
        connection.execute(text("UPDATE leads SET status='Fechado' WHERE status='Vendido'"))

        # Índices novos que podem faltar no banco recuperado.
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_leads_email ON leads (email)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_leads_campaign_id ON leads (campaign_id)"))

        # Como o histórico antigo foi perdido, o banco recuperado passa a representar
        # o estado da migration inicial reconstruída.
        connection.execute(text(
            "CREATE TABLE IF NOT EXISTS alembic_version "
            "(version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
        ))
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": HEAD_REVISION},
        )

    print(f"Recuperação concluída. Banco marcado em {HEAD_REVISION}.")
    print("Agora execute: alembic upgrade head")


if __name__ == "__main__":
    main()
