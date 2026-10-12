"""Saúde da API e integridade das migrations."""

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from database import engine
from models import Base
from tests.conftest import BACKEND_DIR


def test_health_endpoints(client):
    assert client.get("/health").json() == {"status": "online"}
    response = client.get("/health/database")
    assert response.status_code == 200
    assert response.json()["database"] == "online"


def test_database_is_at_alembic_head():
    script = ScriptDirectory.from_config(Config(str(BACKEND_DIR / "alembic.ini")))
    with engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()
    assert current == script.get_current_head()


def test_alembic_has_single_head():
    script = ScriptDirectory.from_config(Config(str(BACKEND_DIR / "alembic.ini")))
    assert len(script.get_heads()) == 1


def test_models_match_migrated_schema():
    """Equivalente a `alembic check`: nenhuma diferença entre models e banco."""
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        differences = compare_metadata(context, Base.metadata)
    assert differences == [], f"Models divergem das migrations: {differences}"


def test_leads_table_has_area_profissional():
    """Regressão: a coluna existia no model mas não na migration inicial."""
    columns = {column["name"] for column in inspect(engine).get_columns("leads")}
    assert "area_profissional" in columns
