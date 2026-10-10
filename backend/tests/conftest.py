"""Configuração dos testes.

Os testes rodam contra um SQLite temporário criado pelas MIGRATIONS do Alembic
(não por `create_all`), para que um schema divergente dos models seja detectado.
As variáveis de ambiente precisam ser definidas ANTES de importar `main`.
"""

import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

_TMP_DIR = tempfile.mkdtemp(prefix="gi-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DIR}/test.db"
os.environ["JWT_SECRET_KEY"] = "chave-de-teste-com-mais-de-32-caracteres-0123456789"
os.environ["APP_ENV"] = "development"
os.environ["FRONTEND_URL"] = "http://localhost:3000"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from database import engine  # noqa: E402
from models import Base  # noqa: E402

ADMIN_EMAIL = "admin@teste.local"
ADMIN_PASSWORD = "senha-admin-123"


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Cria o schema com `alembic upgrade head` uma única vez."""
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    command.upgrade(config, "head")
    yield


@pytest.fixture(autouse=True)
def clean_database(migrated_database):
    """Esvazia todas as tabelas de negócio antes de cada teste."""
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    yield


@pytest.fixture()
def client():
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture()
def upload_dir(tmp_path, monkeypatch):
    """Redireciona uploads para uma pasta temporária."""
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    return tmp_path


def login(client: TestClient, email: str, senha: str) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "senha": senha})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def admin_headers(client):
    response = client.post(
        "/api/auth/bootstrap-admin",
        json={"nome": "Admin", "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD},
    )
    assert response.status_code == 201, response.text
    return login(client, ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture()
def make_user(client, admin_headers):
    """Cria um usuário pelo painel admin e devolve (headers, dados)."""

    def _make(role: str, email: str, lead_id: int | None = None, senha: str = "senha-12345"):
        response = client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "nome": f"Usuário {role}",
                "email": email,
                "senha": senha,
                "role": role,
                "lead_id": lead_id,
                "ativo": True,
            },
        )
        assert response.status_code == 201, response.text
        return login(client, email, senha), response.json()

    return _make


def new_lead_payload(**overrides) -> dict:
    payload = {
        "nome": "Maria Souza",
        "origem": "Instagram",
        "objetivo": "Capacitar a equipe",
        "interesse": "Alto",
        "tipo_cliente": "B2B",
        "empresa": "Acme Ltda",
        "email": "maria@acme.com",
        "consentimento_contato": True,
    }
    payload.update(overrides)
    return payload


@pytest.fixture()
def create_lead(client, admin_headers):
    def _create(**overrides) -> dict:
        response = client.post(
            "/api/leads", headers=admin_headers, json=new_lead_payload(**overrides)
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture()
def course_setup(client, admin_headers):
    """Produto de R$ 147 com curso ativo e 2 conteúdos."""
    product = client.post(
        "/api/products",
        headers=admin_headers,
        json={"nome": "Workshop IA", "preco": 147, "ativo": True},
    )
    assert product.status_code == 201, product.text
    product_id = product.json()["id"]

    course = client.post(
        "/api/courses",
        headers=admin_headers,
        json={"product_id": product_id, "nome": "IA no Dia a Dia", "ativo": True},
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]

    content_ids = []
    for ordem, titulo in ((1, "Abertura"), (2, "Método CLARO")):
        content = client.post(
            f"/api/courses/{course_id}/contents",
            headers=admin_headers,
            json={"titulo": titulo, "tipo": "video", "ordem": ordem},
        )
        assert content.status_code == 201, content.text
        content_ids.append(content.json()["id"])

    return {"product_id": product_id, "course_id": course_id, "content_ids": content_ids}
