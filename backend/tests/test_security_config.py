"""Configuração de segurança: CORS e chave JWT."""

import os
import subprocess
import sys

import pytest

from tests.conftest import BACKEND_DIR


def test_cors_default_allows_only_frontend_in_production(monkeypatch):
    import main

    monkeypatch.setattr(main, "IS_PRODUCTION", True)
    monkeypatch.setattr(main, "FRONTEND_URL", "https://app.exemplo.com")
    monkeypatch.setenv("CORS_ORIGINS", "https://ebook.exemplo.com/, ")
    assert main._build_cors_origins() == ["https://app.exemplo.com", "https://ebook.exemplo.com"]


def test_cors_keeps_live_server_origins_only_in_development(monkeypatch):
    import main

    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.setattr(main, "IS_PRODUCTION", False)
    assert "http://localhost:5500" in main._build_cors_origins()
    monkeypatch.setattr(main, "IS_PRODUCTION", True)
    assert "http://localhost:5500" not in main._build_cors_origins()


def test_cors_preflight_from_unknown_origin_is_not_allowed(client):
    response = client.options(
        "/api/leads",
        headers={
            "Origin": "https://site-malicioso.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def _import_main_in_subprocess(app_env: str, secret: str) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "APP_ENV": app_env,
        "JWT_SECRET_KEY": secret,
        "DATABASE_URL": "sqlite://",
    }
    return subprocess.run(
        [sys.executable, "-c", "import main"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize("secret", ["troque-por-uma-chave-secreta-forte", "curta"])
def test_production_refuses_weak_jwt_secret(secret):
    result = _import_main_in_subprocess("production", secret)
    assert result.returncode != 0
    assert "JWT_SECRET_KEY" in result.stderr


def test_production_accepts_strong_jwt_secret():
    result = _import_main_in_subprocess("production", "x" * 48)
    assert result.returncode == 0, result.stderr


def test_development_still_accepts_short_jwt_secret():
    result = _import_main_in_subprocess("development", "chave-curta-de-dev")
    assert result.returncode == 0, result.stderr
